# -*- encoding: utf-8 -*-
from contextlib import closing

import requests

from lxml import etree


class Node(object):

    def __init__(self, iri):
        self.iri = iri
        self.label = None
        self.parents = []
        self.children = []
        self.max_depth = 0
        self.root_node = False

    def __unicode__(self):
        if self.label is None:
            return self.iri
        else:
            return self.label

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class Owl(object):

    def get_iri(self, e):
        for irikey in ('IRI', 'abbreviatedIRI'):
            if irikey in e.attrib:
                iri = e.attrib[irikey]
                return iri
        raise RuntimeError('IRI not found for element %s' % e)

    def declaration(self, elements, nodes):
        for e in elements:
            iri = self.get_iri(e)
            nodes[iri] = Node(iri)
        return

    def find_node(self, iri):
        if iri in self.nodes:
            return self.nodes[iri]
        if iri in self.data_properties:
            return self.data_properties[iri]
        if iri in self.object_properties:
            return self.object_properties[iri]
        if iri in self.annotations:
            return self.annotations[iri]    
        return None

    def __init__(self, url, already_converted=False):
        self.url = url
        self.already_converted = already_converted
        self.parse()

    def create_input_generator(self):
        content_chunk_size = 8192
        if self.url.startswith('http'):
            if self.already_converted:
                print 'Processing {}'.format(self.url)
                req_url = self.url
                kwargs = {'stream': True}
            else:
                print 'Converting, then processing {}'.format(self.url)
                req_url = 'http://owl.cs.manchester.ac.uk/converter/convert'
                payload = {'ontology': self.url, 'format': 'OWL/XML'}
                kwargs = {'stream': True, 'params': payload}
            with closing(requests.get(req_url, **kwargs)) as response:
                if response.status_code != 200:
                    raise RuntimeError(response.text.encode('utf-8'))
                for chunk in response.iter_content(chunk_size=content_chunk_size, decode_unicode=True):
                    yield chunk
        else:
            self.local_file = True
            with open(self.url) as fileobj:
                while True:
                    chunk = fileobj.read(content_chunk_size)
                    if not chunk:
                        break
                    yield chunk

    def parse(self):
        nsmap = {}
        nsmap_alt = {}
        event_types = ('start', 'end', 'start-ns')
        parser = etree.XMLPullParser(event_types)

        self.nodes = {}
        self.data_properties = {}
        self.object_properties = {}
        self.annotations = {}
        self._subclasses = []
        self._labels = []
        self._comments = []

        xml_depth = 0
        bytes_read = 0
        for i, chunk in enumerate(self.create_input_generator()):
            bytes_read += len(chunk)
            #if i % 100 == 0:
                #print bytes_read
            parser.feed(chunk)

            for event, elem in parser.read_events():
                if event == 'start-ns': # start of a namespace declaration
                    ns, url = elem
                    nsmap[ns] = url
                    if ns == '':
                        nsmap_alt['owl'] = url
                    else:
                        nsmap_alt[ns] = url
                elif event == 'start':
                    xml_depth += 1
                elif event == 'end':
                    if elem.tag == fixtag('', 'Declaration', nsmap):
                        self.declaration(elem.findall('owl:Class', nsmap_alt),
                                         self.nodes)
                        self.declaration(elem.findall('owl:DataProperty', nsmap_alt),
                                         self.data_properties)
                        self.declaration(elem.findall('owl:ObjectProperty', nsmap_alt),
                                         self.object_properties)

                    elif elem.tag == fixtag('', 'SubClassOf', nsmap):
                        classes = elem.findall('owl:Class', nsmap_alt)
                        if len(classes) == 2:
                            subclass_iri = self.get_iri(classes[0])
                            superclass_iri = self.get_iri(classes[1])
                            self._subclasses.append([subclass_iri, superclass_iri])

                    elif elem.tag == fixtag('', 'AnnotationAssertion', nsmap):
                        # is it a label?
                        properties = elem.findall('owl:AnnotationProperty', nsmap_alt)
                        self.declaration(properties, self.annotations)
                        is_label = False
                        is_comment = False
                        num_comments = 0
                        for p in properties:
                            iri = self.get_iri(p)
                            if iri == 'rdfs:label':
                                is_label = True
                            elif iri == 'rdfs:comment':
                                is_comment = True


                        if is_label:
                            # get the label
                            literals = elem.findall(fixtag('', 'Literal', nsmap))
                            if len(literals) == 0:
                                raise RuntimeError('Where is Literal for label %s?' % elem)
                            if len(literals) > 1:
                                raise RuntimeError('Why multiple Literals for label %s?' % elem)
                            label = literals[0].text
                            #print(label)

                            # get IRIs that label will be applied to
                            iris = elem.findall('owl:IRI', nsmap_alt)
                            airis = elem.findall('owl:AbbreviatedIRI', nsmap_alt)
                            self._labels.append([label, [i.text for i in iris + airis]])
                        elif is_comment:
                            # get the literal
                            literals = elem.findall(fixtag('', 'Literal', nsmap))
                            if len(literals) == 0:
                                raise RuntimeError('Where is Literal for  %s?' % elem)
                            if len(literals) > 1:
                                raise RuntimeError('Why multiple Literals for  %s?' % elem)
                            comment = literals[0].text    
                            # get IRIs that comment will be applied to
                            iris = elem.findall('owl:IRI', nsmap_alt)
                            airis = elem.findall('owl:AbbreviatedIRI', nsmap_alt)
                            self._comments.append([comment, [i.text for i in iris + airis]])

                    if xml_depth == 2:
                        # clean up children
                        elem.clear()
                        # clean up preceding siblings
                        while elem.getprevious() is not None:
                            del elem.getparent()[0]
                    xml_depth -= 1

        if not self.nodes:
            raise RuntimeError('No nodes found in document')

        # Apply superclasses and subclasses
        for subclass_iri, superclass_iri in self._subclasses:
            if superclass_iri not in self.nodes:
                self.nodes[superclass_iri] = Node(superclass_iri)
            if subclass_iri not in self.nodes:
                self.nodes[subclass_iri] = Node(subclass_iri)
            self.nodes[superclass_iri].children.append(subclass_iri)
            self.nodes[subclass_iri].parents.append(superclass_iri)

        # Apply labels
        for label, iris in self._labels:
            for iri in iris:
                node = self.find_node(iri)
                if node:
                    node.label = label

        print(len(self._comments))
        
def fixtag(ns, tag, nsmap):
    return '{' + nsmap[ns] + '}' + tag
