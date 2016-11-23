#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# converter.py
#
# Description:
#       Command line interface to http://owl.cs.manchester.ac.uk/converter
#
# Author:
#       Melinda H. McDaniel
#
# Date:
#       Aug 29, 2015
#

# http://owl.cs.manchester.ac.uk/converter/convert?ontology=http://www.co-ode.org/ontologies/pizza/pizza.owl&format=OWL/XML

import argparse
import requests
import sys
import ontparser.rdb

def main():
    formats = [
        'Manchester+OWL+Syntax',
        'OWL/XML',
        'OWL+Functional+Syntax',
        'RDF/XML',
        'Turtle',
        'Latex',
    ]
    arg_parser = argparse.ArgumentParser(
        description=('Command line interface to http://owl.cs.manchester.ac.uk/converter'))
    arg_parser.add_argument('ontology', help='Ontology Physical URI')
    arg_parser.add_argument('format', choices=formats)
    args = arg_parser.parse_args()
    payload = {'ontology': args.ontology, 'format': args.format}
    resp = requests.get('http://owl.cs.manchester.ac.uk/converter/convert', params=payload)
    if resp.status_code != 200:
        sys.stderr.write('Converter failure: %s\n', resp.reason)
        sys.exit(1)
    try:
        print resp.text.encode('utf-8')
    except Exception as ex:
        ontparser.rdb.set_trace()

if __name__ == '__main__':
    main()
