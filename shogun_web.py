from flask import Flask, render_template, redirect, send_from_directory
from flask.ext.assets import Environment, Bundle
from flask_analytics import Analytics
from werkzeug.routing import BaseConverter

from BeautifulSoup import BeautifulSoup
from github import Github
import os
import urllib2, urllib
import json
import base64
import calendar

# initialization
app = Flask(__name__)
# app.config['DEBUG'] = True # enable for local bug hunting
Analytics(app)
app.config['ANALYTICS']['GOOGLE_CLASSIC_ANALYTICS']['ENABLED'] = True
app.config['ANALYTICS']['GOOGLE_CLASSIC_ANALYTICS']['ACCOUNT'] = 'UA-4138452-1'


# api docs regex converter
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

# assets
assets = Environment(app)

scss = Bundle('stylesheets/main.scss', filters='pyscss', output='gen/scss.css')
all_css = Bundle('vendor/*.css', scss, filters='cssmin', output="gen/all.css")
assets.register('css_all', all_css)

js = Bundle(
    'vendor/jquery-3.1.1.min.js',
    'vendor/jquery.timeago.js',
    'vendor/bootstrap.min.js',
    'vendor/showdown.min.js',
    'javascripts/*.js',
    filters='jsmin', output='gen/packed.js'
)
assets.register('js_all', js)

# constants
SHOWCASE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/static/showcase"
NOTEBOOK_DIR = os.path.dirname(os.path.realpath(__file__)) + "/static/notebook/latest"
DEMO_DIR = os.path.dirname(os.path.realpath(__file__)) + "/../shogun-demo"
SHOGUN_IRCLOGS = "/var/www/shogun-toolbox.org/irclogs/"
ARCHIVES_DIR = "/var/www/shogun-toolbox.org/archives/"
DOCS_SUBMODULE_DIR = app.root_path + '/docs/'
COOKBOOK_SUBMODULE_DIR = app.root_path + '/static/cookbook/'
COOKBOOK_PR_SUBMODULE_DIR = app.root_path + '/static/cookbook_pr/'
DOXYGEN_SUBMODULE_DIR = app.root_path + '/static/api/'
NOTEBOOK_SUBMODULE_DIR = app.root_path + "/static/notebook/"

# if dev environment
if (os.environ.get('DEV', None)):
    import pdb

    app.config.update(DEBUG=True)
    DEMO_DIR = os.path.dirname(os.path.realpath(__file__)) + "/static/demos"
    SHOGUN_IRCLOGS = os.path.dirname(os.path.realpath(__file__)) + '/static/irclogs'


@app.route('/docs/<path:filename>')
def docs_static(filename):
    print app.root_path
    return send_from_directory(DOCS_SUBMODULE_DIR, filename)


@app.route('/examples')
@app.route('/examples/<path:filename>')
@app.route('/cookbook/<path:filename>')
def cookbook_static(filename=None):
    if filename is None:
        return redirect('/examples/latest/index.html')
    return send_from_directory(COOKBOOK_SUBMODULE_DIR, filename)


@app.route('/cookbook_pr/<path:filename>')
def cookbook_pr_static(filename):
    return send_from_directory(COOKBOOK_PR_SUBMODULE_DIR, filename)


@app.route('/api/<path:filename>')
def api_static(filename):
    return send_from_directory(DOXYGEN_SUBMODULE_DIR, filename)


@app.route('/notebook/<path:filename>')
def notebook_static(filename):
    return send_from_directory(NOTEBOOK_SUBMODULE_DIR, filename)


@app.route('/archives/<path:filename>')
def archives_static(filename):
    return send_from_directory(ARCHIVES_DIR, filename)


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/showroom')
def showroom():
    notebooks = get_notebooks()
    return render_template('showroom.html', examples=notebooks)


@app.route('/api')
def api():
    return redirect('/api/latest/classes.html')

@app.route('/docs')
def docs():
    return redirect('https://github.com/shogun-toolbox/shogun/wiki')

@app.route('/mission')
def mission():
    return render_template('mission.html')

@app.route('/doc/en/<path:filename>')
def doc(filename):
    if filename.startswith('current'):
        filename = filename.replace('current', 'latest')
    return redirect('/api/{path}'.format(path=filename))


@app.route('/install')
def install():
    return render_template('install.html')


@app.route('/irclogs')
def irclogs():
    logfiles = [f.replace('#shogun.', '').replace('.log.html', '') for f in os.listdir(SHOGUN_IRCLOGS) if
                f.startswith('#shogun')]
    logfiles.sort()

    logfiles = get_calendar_irc_logs(logfiles)

    return render_template('irclogs.html', logs=logfiles)


@app.route('/irclog/<date>/')
def irclog(date):
    logfile = '%s/#shogun.%s.log.html' % (SHOGUN_IRCLOGS, date)
    html = open(logfile).read()
    soup = BeautifulSoup(html)
    log = str(soup.body.table)
    return render_template('irclogs.html', log=log)


@app.route('/<regex("(SG|C).*"):class_name>/')
def api_redirect(class_name):
    if class_name.startswith('C'):
        doxygen_prefix = "classshogun_1_1"
    else:
        doxygen_prefix = "singletonshogun_1_1"
    return redirect('/api/latest/{prefix}{sg_class}.html'.format(
        prefix=doxygen_prefix, sg_class=class_name)
    )


# utils
def get_notebooks():
    notebooks = []
    rel_path = "/notebook/latest/"
    for _file in os.listdir(NOTEBOOK_DIR):
        if _file.endswith(".html"):
            notebook_url = rel_path + _file
            notebook_image = notebook_url[:-5] + '.png'
            notebook_title = _file[0:-5].replace('_', ' ')
            notebook_abstract = get_abstract(os.path.join(NOTEBOOK_DIR, _file.replace('.html', '.ipynb')))

            notebooks.append({
                'url': notebook_url,
                'image': notebook_image,
                'title': notebook_title,
                'abstract': notebook_abstract})

    return notebooks


def get_abstract(fname):
    import json
    import os
    import markdown

    try:
        js = json.load(file(fname))

        if 'worksheets' in js:
            if len(js['worksheets']) > 0:
                if js['worksheets'][0]['cells'] is not None:
                    cells = js['worksheets'][0]['cells']
        else:
            if 'cells' in js:
                cells = js['cells']

        for cell in cells:
            if cell['cell_type'] == 'heading' or cell['cell_type'] == 'markdown':
                return markdown.markdown(''.join(cell['source']).replace('#',''))
    except:
        pass
    return os.path.basename(fname)


# make sure to use the 'raw' file url
def get_github_file(url):
    request = urllib2.Request(url)

    try:
        response = urllib2.urlopen(request)
        return response.read().decode('utf-8')
    except urllib2.HTTPError, e:
        print e


def get_calendar_irc_logs(logfiles):
    logfiles_set = set(logfiles)
    cal = calendar.Calendar()
    start_entry = logfiles[0]
    end_entry = logfiles[-1]
    start_year = int(start_entry[:4])
    start_month = int(start_entry[5:7])
    end_year = int(end_entry[:4])
    end_month = int(end_entry[5:7])

    all_entries = []
    for year in xrange(start_year, end_year + 1):
        cur_start_month = 1
        cur_end_month = 12

        if year == start_year:
            cur_start_month = start_month
        if year == end_year:
            cur_end_month = end_month

        year_entries = []
        for month in xrange(cur_start_month, cur_end_month + 1):
            month_entries = []

            weeks_entries = []
            week_entries = []
            weekday = 0
            for day in cal.itermonthdays(year, month):
                weekday += 1
                entry = ["", "", ""]
                if day > 0:
                    key = '%04d-%02d-%02d' % (year, month, day)
                    entry = [day, "", ""]
                    if key in logfiles_set:
                        entry[1:3] = key, os.path.getsize(SHOGUN_IRCLOGS + '/' + '#shogun.%s.log.html' % key) / 1024
                week_entries.append(entry)
                if (weekday > 0) and (weekday % 7 == 0):
                    weeks_entries.append(week_entries)
                    week_entries = []

            if len(week_entries) > 0:
                weeks_entries.append(week_entries)
            month_entries = [weeks_entries]
            year_entries.append((calendar.month_name[month], month_entries))
        all_entries.append((year, year_entries[::-1]))

    return all_entries[::-1]


# launch
if __name__ == '__main__':
    app.run()
