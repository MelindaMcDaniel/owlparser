#!/usr/bin/env python
import argparse
import json
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
    arg_parser.add_argument('--already_converted',
                            action='store_true',
                            help='already converted')
    arg_parser.add_argument('--debug',
                            action='store_true',
                            help='print more info on server')
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
    params['already_converted'] = args.already_converted
    params['debug'] = args.debug
    r = requests.get(owlparser_url, params=params)

    print('\nRequest:\n\n%s' % r.url)
    print('\nResponse:\n')
    print json.dumps(r.json(), sort_keys=True, separators=(',', ': '), indent=4)


if __name__ == '__main__':
    main()
