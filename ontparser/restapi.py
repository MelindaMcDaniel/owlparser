from flask_restful import Resource, Api, reqparse, inputs

from ontparser import app
from ontparser.quality import owl_quality


api = Api(app)


class Main(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, help='url cannot be blank!')
        parser.add_argument('exclude_semiotic_layer', action='append')
        parser.add_argument('domain')
        parser.add_argument('already_converted', type=inputs.boolean, default=False)
        parser.add_argument('debug', type=inputs.boolean, default=False)  # remove this when in production
        args = parser.parse_args()
        semiotic_quality_flags = {'syntactic', 'semantic', 'pragmatic', 'social'}
        if args.exclude_semiotic_layer:
            exclude_semiotic_layer = set(args.exclude_semiotic_layer)
        else:
            exclude_semiotic_layer = set()
        if exclude_semiotic_layer & semiotic_quality_flags != exclude_semiotic_layer:
            raise ValueError(
                'Invalid semiotic layer. Must be one of: {}.'.format(', '.join(semiotic_quality_flags)))
        return owl_quality(args.url, semiotic_quality_flags - exclude_semiotic_layer,
                           args.domain, already_converted=args.already_converted, debug=args.debug)


api.add_resource(Main, '/rest/execute')
