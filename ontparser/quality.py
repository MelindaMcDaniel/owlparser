# -*- encoding: utf-8 -*-
import os

from ontparser.owlparser import Owl

# we put the nltk data in a non-standard location, which requires that
# we set an environment variable indicating where the data will be
# found:
script_dir = os.path.dirname(os.path.realpath(__file__))
os.environ['NLTK_DATA'] = os.path.join(script_dir, '..', 'nltk_data')
from nltk.corpus import wordnet as wn  # noqa: E402


def set_wn_synonym_count(node):
    if node.label:
        node.wn_count = len(wn.synsets(node.label))
    else:
        node.wn_count = 0

def set_synset_list(node):
    synonym_list = []
    if (node.label):
        print("Label" + node.label)
        print(len(wn.synsets(node.label)))
    else:
        print("none")
    print(len(wn.synsets("be")))
    if node.label:
        for synset in wn.synsets(node.label):
            fullname = synset.name()
            fulltuple = fullname.partition('.')
            synonym_list.append(fulltuple[0])
    print ("number of synonyms: " + str(len(synonym_list)))
    return synonym_list

def get_synonyms(word):
    synonym_list = []
    for synset in wn.synsets(word):
        fullname = synset.name()
        fulltuple = fullname.partition('.')
        if not fulltuple[0] in synonym_list:
            synonym_list.append(fulltuple[0])
    return synonym_list

def split_words(domain):
    return filter(lambda z: len(z), [x.strip() for x in domain.split(',')])

def set_domain_synset_list(domain):
    synonym_list = []
    for keyword in split_words(domain):
        synonym_list.extend(get_synonyms(keyword))
    return synonym_list

class OwlQuality(object):

    def __init__(self, nodes, object_properties, data_properties, annotations, average_annotation_length,
            comments,average_comment_length, semiotic_quality_flags=None, domain=None):
        self.nodes = nodes
        self.object_properties = object_properties
        self.data_properties = data_properties
        self.annotations = annotations
        self.comments = comments
        self.domain = domain
        self.complete_synonym_list = []
        self.domain_matches = 0
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

        # get number of synonyms for each one and create unique set of synonyms
        self.count_definitions = 0
        self.count_defined = 0
        for node in self.nodes.itervalues():
            print(node)
            set_wn_synonym_count(node)  # count number of synonyms
            temp_synonym_list = set_synset_list(node) # create synonym list
            for item in temp_synonym_list:
                if item not in self.complete_synonym_list:
                    self.complete_synonym_list.append(item)   # create unique list
                    print('adding ' + str(item))
            if node.wn_count > 0:
                self.count_defined += 1
            self.count_definitions += node.wn_count

        total_comment_length = 0
        for comment in self.comments:
            total_comment_length += len(comment)
        if len(self.comments) > 0:
            self.average_comment_length = total_comment_length/len(self.comments)
        else:
            self.average_comment_length = 0

        total_annotation_length = 0
        for annotation in self.annotations:
            total_annotation_length += len(annotation)
        if len(self.annotations) > 0:
            self.average_annotation_length = total_annotation_length/len(self.annotations)
        else:
            self.average_annotation_length = 0

        # get number of nodes that match the domain or a synonym of the domain

        if domain:
          for item in set_domain_synset_list(domain):
             self.domain_matches += sum(1 for node in self.nodes.itervalues()
                                       if unicode(item).lower() in unicode(node).lower())
             self.domain_matches += sum(1 for node in self.object_properties.itervalues()
                                       if item.lower() in unicode(node).lower())
             self.domain_matches += sum(1 for node in self.data_properties.itervalues()
                                        if item.lower() in unicode(node).lower())
             self.domain_matches += sum(1 for node in self.annotations.itervalues()
                                        if item.lower() in unicode(node).lower())
             self.domain_matches += sum(1 for node in self.comments
                                        if item.lower() in unicode(node).lower())
        else:
            self.domain_matches = 0

        self.semiotic_metric_value_computation()

    def semiotic_metric_value_computation(self):

        num_classes = len(self.nodes)
        num_subclasses = num_classes - len(self.root_nodes)
        num_attributes = len(self.object_properties) + len(self.data_properties)
        num_annotations = len(self.annotations)

        # ---- Syntactic Layer ----
        self.lawfulness = 1.0 # no breached rules or it wouldn't parse
        # structure - ratio of subclasses to classes
        if num_subclasses > 0:
            self.structure = round(float(num_subclasses) / num_classes,3)
        else:
            self.structure = 0.0
        # Two types of richness:
        # relationship richness = numnoninheritance / (numinheritance +
        # numnoninheritance)
        total_relationships = num_attributes + num_subclasses
        if total_relationships > 0:
            self.relationship_richness = round(float(num_attributes) / total_relationships,3)
        else:
            self.relationship_richness = 0.0

        # Attribute Richness = attributes/classes
        if num_classes > 0:
            self.attribute_richness = round(float(num_attributes) / len(self.nodes),3)
        else:
            self.attribute_richness = 0.0

        # Overall Richness = average of both
        self.overall_richness = round(((self.relationship_richness +
                                 self.attribute_richness) / 2.0),3)

        self.overall_syntactic = round(((self.overall_richness + self.structure + self.lawfulness) / 3.0),3)

        if self.overall_syntactic > 1.0:
            self.overall_syntactic = 1

        # ---- SEMANTIC layer ----
        self.consistency = 1.0  # none of these have inconsistencies
        # clarity = total number of wordnet definitions/classes
        self.clarity = round(float(self.count_definitions) / len(self.nodes),3)

        # interpretability = percentage of classes found in wordnet = definedclasses/classes
        self.interp = round(float(self.count_defined) / len(self.nodes),3)

        # precision - ratio of defined words to total number of definitions (1:1 is best)
        if self.count_definitions > 0:
            self.precision = round(float(self.count_defined) / float(self.count_definitions),3)
        else:
            self.precision = 0.0
        self.overall_semantic = round((self.consistency + self.interp + self.precision)/3.0,3)

        if self.overall_semantic > 1.0:
            self.overall_semantic = 1

        # ---- PRAGMATIC Layer ----
        # adaptability (aka cohesion) number of ratio of leaf nodes to regular nodes combined with
        # ratio of average leaf node depth to all nodes
        self.cohesion1 = float(self.avg_leaf_node_depth)/self.deepest_leaf_node
        self.cohesion2 = float(len(self.leaf_nodes))/len(self.nodes)

        self.adaptability = round((self.cohesion1 + self.cohesion2) /2.0, 3)
        #self.comprehensiveness = round(num_classes/113307.0, 3); # 113307 is the max number of classes in the testing set so this value is normalized
        self.comprehensiveness = round(len(self.complete_synonym_list)/(len(self.nodes)+num_attributes),3) # new definition - comprehensiveness = number of synonyms represented/(nodes+attributes)

        self.ease_of_use =  round(float(len(self.comments))/(num_classes+num_attributes+num_annotations),3)
        #self.ease_of_use = self.average_comment_length + self.average_annotation_length
        if self.ease_of_use > 1.0:
            self.ease_of_use = 1.0
        self.relevance = round(float(self.domain_matches)/(num_classes+num_attributes+num_annotations),3)

        if self.domain:
            self.overall_pragmatic = round((self.adaptability + self.relevance + self.ease_of_use) / 3.0,3)
        else:
            self.overall_pragmatic = round((self.adaptability + self.ease_of_use)/2.0,3) # don't count off for relevance if no domain entered

        if self.overall_syntactic > 1.0:
            self.overall_syntactic = 1

        self.overall_social = 0.0   # fix this later

        # compute overall_quality
        if len(self.semiotic_quality_flags):
            filtered_quality_flags = [getattr(self, 'overall_%s' % sqf)
                                      for sqf in self.semiotic_quality_flags]
            self.overall = round(sum(filtered_quality_flags) / float(len(filtered_quality_flags)),3)
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


def owl_quality(url, semiotic_quality_flags, domain, debug=False, already_converted=False):
    owl = Owl(url, already_converted)
    quality = OwlQuality(owl.nodes, owl.object_properties, owl.data_properties, owl.annotations,owl.average_annotation_length, owl._comments,owl.average_comment_length,
                         semiotic_quality_flags, domain)
    if debug:
        quality.print_tree()
        quality.print_labeled()
        quality.print_unlabeled()

    return {
        'counts': {
            '10. number of synonyms': quality.complete_synonym_list,
            '11. number of defined terms':quality.count_defined,
            '10. average_comment_length': quality.average_comment_length,
            '11. average_annotation_length': quality.average_annotation_length,
            '1. node_count': len(quality.nodes),
            '1.1 root_node_count': len(quality.root_nodes),
            '1.2 leaf_node_count': len(quality.leaf_nodes),
            '2. deepest_leaf_node': quality.deepest_leaf_node,
            '3. avg_leaf_node_depth': quality.avg_leaf_node_depth,
            '4. object_property_count': len(quality.object_properties),
            '5. data_property_count': len(quality.data_properties),
            '6. annotations': len(quality.annotations),
            '7. domain_matches': quality.domain_matches,
            '8. comments': len(quality.comments),
            '9. attribute_richness': quality.attribute_richness,
            '9.1. relationship_richness': quality.relationship_richness,

        },
        'semiotic_ontology_metrics': {
            '0 Overall Quality': quality.overall,
            '1 Syntactic Quality': quality.overall_syntactic,
            '1.1 Lawfulness': quality.lawfulness,
            '1.2 Richness': quality.overall_richness,
            '1.3 Structure': quality.structure,
            '2 Semantic Quality': quality.overall_semantic,
            '2.1 Consistency': quality.consistency,
            '2.2 interpretability': quality.interp,
            '2.3 Precision': quality.precision,
            '3 Pragmatic Quality': quality.overall_pragmatic,
            '3.1 Accuracy': None,
            '3.2 Adaptability': quality.adaptability,
            '3.3 Comprehensiveness': quality.comprehensiveness,
            '3.4 Ease of Use': quality.ease_of_use,
            '3.5 Relevance': quality.relevance,
            '4 Social Quality': quality.overall_social,
            '4.1 Authority': None,
            '4.2 History': None,
            '4.3 Recognition': None,
        }
    }
