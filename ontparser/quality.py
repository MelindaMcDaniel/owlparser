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


class OwlQuality(object):

    def __init__(self, nodes, object_properties, data_properties, annotations,
                 semiotic_quality_flags=None, keyword=None):
        self.nodes = nodes
        self.object_properties = object_properties
        self.data_properties = data_properties
        self.annotations = annotations
        self.keyword = keyword
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
            set_wn_synonym_count(node)  # count number of synonyms 
            if node.wn_count > 0:
                self.count_defined += 1
            self.count_definitions += node.wn_count

        # get number of nodes that match the keyword
        if keyword:
             self.keyword_matches = sum(1 for node in self.nodes.itervalues()
                                       if keyword.lower() in unicode(node).lower())
             self.keyword_matches += sum(1 for node in self.object_properties.itervalues()
                                       if keyword.lower() in unicode(node).lower())
             self.keyword_matches += sum(1 for node in self.data_properties.itervalues()
                                        if keyword.lower() in unicode(node).lower())   
             self.keyword_matches += sum(1 for node in self.annotations.itervalues()
                                        if keyword.lower() in unicode(node).lower())                       
        else:
            self.keyword_matches = 0

        self.semiotic_metric_value_computation()

    def semiotic_metric_value_computation(self):

        num_classes = len(self.nodes)
        num_subclasses = num_classes - len(self.root_nodes)
        num_attributes = len(self.object_properties) + len(self.data_properties)
        num_annotations = len(self.annotations)

        # ---- Syntactic Layer ----
        # structure - ratio of subclasses to classes
        if num_subclasses > 0:
            self.structure = round(float(num_classes) / num_subclasses,3)
        else:
            self.structure = 0.0
        # Two types of richness:    
        # relationship richness = numinheritance / (numinheritance +
        # numnoninheritance)
        total_relationships = num_attributes + num_subclasses
        if total_relationships > 0:
            self.relationship_richness = round(float(num_subclasses) / total_relationships,3)
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

        self.overall_syntactic = round(((self.overall_richness + self.structure) / 2.0),3) 

        # ---- SEMANTIC layer ----
        # clarity = total number of wordnet definitions/classes
        self.clarity = round(float(self.count_definitions) / len(self.nodes),3)

        # interpretability = percentage of classes found in wordnet = definedclasses/classes
        self.interp = round(float(self.count_defined) / len(self.nodes),3)
        
        # precision - ratio of defined words to total number of definitions (1:1 is best)
        if self.count_definitions > 0:
            self.precision = round(float(self.count_defined) / float(self.count_definitions),3)
        else:
            self.precision = 0.0
        self.overall_semantic = round((self.interp + self.precision)/2.0,3)

        # ---- PRAGMATIC Layer ----
        # accuracy (aka cohesion) number of ratio of leaf nodes to regular nodes combined with
        # ratio of leaf nodes to all nodes
        self.cohesion1 = float(self.avg_leaf_node_depth)/self.deepest_leaf_node
        self.cohesion2 = float(len(self.leaf_nodes))/len(self.nodes)
        
        self.adaptability = round((self.cohesion1 + self.cohesion2) /2.0, 3)

        self.ease_of_use = round(float(num_annotations)/(num_classes+num_attributes+num_annotations),3)
        
        self.relevance = round(float(self.keyword_matches)/(num_classes+num_attributes+num_annotations),3)

        if self.keyword:
            self.overall_pragmatic = round((self.adaptability + self.relevance) / 2.0,3)
        else:
            self.overall_pragmatic = round(self.adaptability,3) # don't count off for relevance if no keyword entered
                

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
    quality = OwlQuality(owl.nodes, owl.object_properties, owl.data_properties, owl.annotations,
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
            '5. data_property_count': len(quality.data_properties),
            '6. annotations': len(quality.annotations),
            '7. keyword_matches': quality.keyword_matches,
        },
        'semiotic_ontology_metrics': {
            '0 Overall Quality': quality.overall,
            '1 Syntactic Quality': quality.overall_syntactic,
            '1.1 Lawfulness': None,
            '1.2 Richness': quality.overall_richness,
            '1.3 Structure': quality.structure,
            '2 Semantic Quality': quality.overall_semantic,
            '2.1 Consistency': None,
            '2.2 interpretability': quality.interp,
            '2.3 Precision': quality.precision,
            '3 Pragmatic Quality': quality.overall_pragmatic,
            '3.1 Accuracy': None,
            '3.2 Adaptability': quality.adaptability,
            '3.3 Comprehensiveness': None,
            '3.4 Ease of Use': quality.ease_of_use,
            '3.5 Relevance': quality.relevance,           
            '4 Social Quality': quality.overall_social,
            '4.1 Authority': None,
            '4.2 History': None,
            '4.3 Recognition': None,            
        }
    }
