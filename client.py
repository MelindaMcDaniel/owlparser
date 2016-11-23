#!/usr/bin/env python
import argparse
import pprint
import requests


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('ontology_url',
                            help='url for the OWL/XML file')
    arg_parser.add_argument('--localhost',
                            action='store_true',
                            help='use localhost rather than owlparser.herokuapp.com')
    arg_parser.add_argument('--domain',
                            help='domain to be considered')
    arg_parser.add_argument('--exclude_semiotic_layer',
                            action='append',
                            choices=['syntactic', 'semantic', 'pragmatic', 'social'],
                            help='semiotic layers to be excluded')
    args = arg_parser.parse_args()
    if args.localhost:
        owlparser_url = 'http://localhost:5000/rest/execute'
    else:
        owlparser_url = 'https://owlparser.herokuapp.com/rest/execute'
    params = {'url': args.ontology_url}
    if args.domain:
        params['domain'] = args.domain
    if args.exclude_semiotic_layer:
        params['exclude_semiotic_layer'] = args.exclude_semiotic_layer
    r = requests.get(owlparser_url, params=params)

    print('\nRequest:\n\n%s' % r.url)
    print('\nResponse:\n')
    pprint.pprint(r.json())


if __name__ == '__main__':
    main()
