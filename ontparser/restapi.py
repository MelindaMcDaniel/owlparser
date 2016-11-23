from flask_restful import Resource, Api, reqparse
from ontparser import app
from ontparser.owlparser import owl_quality


api = Api(app)


class Main(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url')
        parser.add_argument('exclude_semiotic_layer', action='append')
        parser.add_argument('domain')
        args = parser.parse_args()
        semiotic_quality_flags = {'syntactic', 'semantic', 'pragmatic', 'social'}
        if args.exclude_semiotic_layer:
            exclude_semiotic_layer = set(args.exclude_semiotic_layer)
        else:
            exclude_semiotic_layer = set()
        if exclude_semiotic_layer & semiotic_quality_flags != exclude_semiotic_layer:
            raise ValueError('Invalid semiotic layer %s. Must be one of %s.' %
                             (excluded, ', '.join(all_semiotic_quality_flags)))
        return owl_quality(args.url, semiotic_quality_flags - exclude_semiotic_layer, args.domain)


api.add_resource(Main, '/rest/execute')
