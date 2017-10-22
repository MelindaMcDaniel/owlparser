from json import dumps

from flask import render_template, request

from ontparser import app
from ontparser.quality import owl_quality


def process_form(request):
    flags = ('syntactic', 'semantic', 'pragmatic', 'social')
    semiotic_quality_flags = {flag for flag in flags if flag in request.form}
    domain = request.form['term'].strip()
    already_converted = 'already_converted' in request.form
    oq = owl_quality(request.form['url'], semiotic_quality_flags, domain, already_converted=already_converted)
    return html_report(oq)


def html_report(oq):
    # just do a json dump for now
    # dumped = dumps(oq, sort_keys=True, separators=(',', ': '), indent=4)
    # return '<pre>%s</pre>' % dumped
    return render_template('results.html', oq=oq)


@app.route('/', methods=['GET', 'POST'])
def gui():
    if request.method == 'POST':
        return process_form(request)
    else:
        return render_template('main.html')


@app.route('/about')
def about():
    return render_template('about.html', name='Melinda McDaniel', date='2017')


@app.route('/layout_test')
def layout_test():
    return render_template('layout.html')


# 0 Overall Quality   0.446
# 1 Syntactic Quality 0.658
# 1.1 Lawfulness      1.0
# 1.2 Richness        0.0
# 1.3 Structure       0.974
# 2 Semantic Quality 0.695
# 2.1 Consistency 1.0
# 2.2 interpretability 0.795
# 2.3 Precision 0.29
# 3 Pragmatic Quality 0.431
# 3.1 Accuracy null
# 3.2 Adaptability 0.863
# 3.3 Comprehensiveness 1.0
# 3.4 Ease of Use 0.0
# 3.5 Relevance 0.0
# 4 Social Quality 0.0
# 4.1 Authority null
# 4.2 History null
# 4.3 Recognition null
# }




# {{ oq['semiotic_ontology_metrics']['2 Semantic Quality'] }}
