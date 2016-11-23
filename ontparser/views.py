from json import dumps

from flask import render_template, request

from ontparser import app
from ontparser.quality import owl_quality


def process_form(request):
    flags = ('syntactic', 'semantic', 'pragmatic', 'social')
    semiotic_quality_flags = {flag for flag in flags if flag in request.form}
    domain = request.form['term'].strip()
    oq = owl_quality(request.form['url'], semiotic_quality_flags, domain)
    return html_report(oq)


def html_report(oq):
    # just do a json dump for now
    dumped = dumps(oq, sort_keys=True, indent=4)
    return '<pre>%s</pre>' % dumped


@app.route('/', methods=['GET', 'POST'])
def gui():
    if request.method == 'POST':
        return process_form(request)
    else:
        return render_template('main.html')


@app.route('/about')
def about():
    return render_template('about.html', name='Melinda H. McDaniel', date='2016')


@app.route('/layout_test')
def layout_test():
    return render_template('layout.html')
