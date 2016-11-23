#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# ontology_parser.py
#
# Description:
#       Simple XML parser for ontologies
#
# Author:
#       Melinda H. McDaniel
#
# Date:
#       Aug 29, 2015
#

from contextlib import closing
import os
import requests
from lxml import etree

# we put the nltk data in a non-standard location, which requires that
# we set an environment variable indicating where the data will be
# found:
script_dir = os.path.dirname(os.path.realpath(__file__))
os.environ['NLTK_DATA'] = os.path.join(script_dir, '..', 'nltk_data')
from nltk.corpus import wordnet as wn


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

    def set_wn_synonym_count(self):
        if self.label:
            self.wn_count = len(wn.synsets(self.label))
        else:
            self.wn_count = 0


class OwlQuality(object):

    def __init__(self, nodes, object_properties, datatype_properties,
                 semiotic_quality_flags=None, keyword=None):
        self.nodes = nodes
        self.object_properties = object_properties
        self.datatype_properties = datatype_properties
        if semiotic_quality_flags is None:
            self.semiotic_quality_flags = set()
        else:
            self.semiotic_quality_flags = semiotic_quality_flags

        self.leaf_nodes = {
            k: v for k, v in self.nodes.iteritems() if len(v.children) == 0
        }

        # calculate max_depth for all leaf nodes
        for node in self.leaf_nodes.itervalues():
            node.max_depth = self.get_max_depth(node)

        self.root_nodes = {
            k: v for k, v in self.nodes.iteritems() if v.root_node
        }

        # for leaf nodes, find average depth and deepest one
        num_leaf_nodes = len(self.leaf_nodes)
        if num_leaf_nodes:
            self.deepest_leaf_node = max(
                v.max_depth for v in self.leaf_nodes.itervalues())
            self.avg_leaf_node_depth = float(
                sum(v.max_depth for v in self.leaf_nodes.itervalues())) / num_leaf_nodes
        else:
            self.deepest_leaf_node = 0
            self.avg_leaf_node_depth = 0

        # get number of synonyms for each one
        self.count_definitions = 0
        self.count_defined = 0
        for node in self.nodes.itervalues():
            node.set_wn_synonym_count()
            if node.wn_count > 0:
                self.count_defined += 1
            self.count_definitions += node.wn_count

        # get number of nodes that match the keyword
        if keyword:
            self.keyword_matches = sum(1 for node in self.nodes.itervalues()
                                       if keyword.lower() in unicode(node).lower())
        else:
            self.keyword_matches = 0

        self.semiotic_metric_value_computation()

    def semiotic_metric_value_computation(self):

        num_classes = len(self.nodes)
        num_subclasses = num_classes - len(self.root_nodes)
        num_attributes = len(self.object_properties) + len(self.datatype_properties)

        ##### Syntactic Layer
        # relationship richness = numinheritance / (numinheritance +
        # numnoninheritance)
        total_relationships = num_attributes + num_subclasses
        if total_relationships > 0:
            self.relationship_richness = float(num_subclasses) / total_relationships
        else:
            self.relationship_richness = 0
        # inheritance richness = num_subclasses/classes
        if num_subclasses > 0:
            self.inheritance_richness = float(num_classes) / num_subclasses
        else:
            self.inheritance_richness = 0
        # Attribute Richness = attributes/classes
        if num_classes > 0:
            self.attribute_richness = float(num_attributes) / num_classes
        else:
            self.attribute_richness = 0

        # Overall Richness = average of all three
        self.overall_richness = (self.relationship_richness +
                                 self.inheritance_richness +
                                 self.attribute_richness) / 3.0

        self.overall_syntactic = self.overall_richness  # fix this later

        ##### SEMANTIC layer
        # clarity = total number of wordnet definitions/classes
        self.clarity = float(self.count_definitions) / len(self.nodes)

        # interpretability = percentage of classes found in wordnet = definedclasses/classes
        self.interp = float(self.count_defined) / len(self.nodes)

        self.overall_semantic = (self.clarity + self.interp)/2.0

        ##### PRAGMATIC Layer
        # cohesion = average depth of a leaf node
        self.cohesion = self.avg_leaf_node_depth

        self.relevance = float(self.keyword_matches) / len(self.nodes)

        self.overall_pragmatic = (self.cohesion + self.relevance) / 2.0   # fix this later

        self.overall_social = 0   # fix this later

        # compute overall_quality
        if len(self.semiotic_quality_flags):
            filtered_quality_flags = [getattr(self, 'overall_%s' % sqf)
                                      for sqf in self.semiotic_quality_flags]
            self.overall = sum(filtered_quality_flags) / float(len(filtered_quality_flags))
        else:
            self.overall = 0.0

    def get_max_depth(self, node_value, depth=0):
        if len(node_value.parents) == 0:
            node_value.root_node = True
            return depth
        max_depth = depth
        for pname in node_value.parents:
            p_depth = depth + 1
            p_depth = self.get_max_depth(self.nodes[pname], p_depth)
            max_depth = max(max_depth, p_depth)
        return max_depth

    def print_node_tree(self, node, level=0):
        print '  ' * level + ('%s (%d)' % (node, node.wn_count))
        for child_name in node.children:
            child_node = self.nodes[child_name]
            self.print_node_tree(child_node, level + 1)

    def print_tree(self, level=0):
        for node in self.root_nodes.itervalues():
            # do not print stand-alone trees
            if node.children:
                print '------'
                print ' Tree'
                print '------'
                self.print_node_tree(node)

    def print_labeled(self):
        print '-----------------------'
        print ' Labeled Nodes (by IRI)'
        print '-----------------------'
        # sort by iri, not label
        for node in sorted([n for n in self.nodes.itervalues() if n.label],
                           key=lambda node: node.iri):
            print '%s %s' % (node.iri, node)

    def print_unlabeled(self):
        print '-----------------'
        print ' Unlabeled Nodes'
        print '-----------------'
        # sort by iri, not label
        for node in sorted([n for n in self.nodes.itervalues() if not n.label],
                           key=lambda node: node.iri):
            print node.iri


class Owl(object):

    CONTENT_CHUNK_SIZE = 10 * 1024

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
        return None

    def __init__(self, fileobj):
        nsmap = {}
        nsmap_alt = {}
        event_types = ('start', 'end', 'start-ns')
        parser = etree.XMLPullParser(event_types)

        self.nodes = {}
        self.data_properties = {}
        self.object_properties = {}
        self._subclasses = []
        self._labels = []

        xml_depth = 0
        while True:
            chunk = fileobj.read(self.CONTENT_CHUNK_SIZE)
            if not chunk:
                break
            parser.feed(chunk)
            for event, elem in parser.read_events():
                if event == 'start-ns':
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
                        is_label = False
                        for p in properties:
                            iri = self.get_iri(p)
                            if iri == 'rdfs:label':
                                is_label = True
                                break

                        if is_label:
                            # get the label
                            literals = elem.findall(fixtag('', 'Literal', nsmap))
                            if len(literals) == 0:
                                raise RuntimeError('Where is Literal for label %s?' % elem)
                            if len(literals) > 1:
                                raise RuntimeError('Why multiple Literals for label %s?' % elem)
                            label = literals[0].text

                            # get IRIs that label will be applied to
                            iris = elem.findall('owl:IRI', nsmap_alt)
                            airis = elem.findall('owl:AbbreviatedIRI', nsmap_alt)
                            self._labels.append([label, [i.text for i in iris + airis]])

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


def fixtag(ns, tag, nsmap):
    return '{' + nsmap[ns] + '}' + tag


def owl_quality(url, semiotic_quality_flags, domain, debug=False):
    if url.startswith('http'):
        with closing(requests.get(url, stream=True)) as response:
            if response.status_code != 200:
                raise RuntimeError(response.text.encode('utf-8'))
            owl = Owl(response.raw)
    else:
        # did not start with http; assume this is a local file
        with open(url) as fileobj:
            owl = Owl(fileobj)

    quality = OwlQuality(owl.nodes, owl.object_properties, owl.data_properties,
                         semiotic_quality_flags, domain)
    if debug:
        quality.print_tree()
        quality.print_labeled()
        quality.print_unlabeled()

    return {
        'counts': {
            '1. node_count': len(quality.nodes),
            '1.1 root_node_count': len(quality.root_nodes),
            '1.2 leaf_node_count': len(quality.leaf_nodes),
            '2. deepest_leaf_node': quality.deepest_leaf_node,
            '3. avg_leaf_node_depth': quality.avg_leaf_node_depth,
            '4. object_property_count': len(quality.object_properties),
            '5. datatype_property_count': len(quality.datatype_properties),
        },
        'semiotic_ontology_metrics': {
            '1. overall_syntactic': quality.overall_syntactic,
            '1.1 relationship_richness': quality.relationship_richness,
            '1.2 inheritance_richness': quality.inheritance_richness,
            '1.3 attribute_richness': quality.attribute_richness,
            '2. overall_semantic': quality.overall_semantic,
            '2.1 clarity': quality.clarity,
            '2.2 interpretability': quality.interp,
            '3. overall_pragmatic': quality.overall_pragmatic,
            '3.1 relevance': quality.relevance,
            '3.2 adaptability': quality.cohesion,
            '4. overall_social': quality.overall_social,
            '5. overall_quality_including_weights': quality.overall,
        }
    }
