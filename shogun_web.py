from flask import Flask, render_template, redirect
from flask.ext.assets import Environment, Bundle

from BeautifulSoup import BeautifulSoup
from github import Github
import os
import urllib2, urllib
import json
import base64
import calendar

# initialization
app = Flask(__name__)
#app.config['DEBUG'] = True # enable for local bug hunting

# assets
assets = Environment(app)

scss = Bundle('stylesheets/main.scss', filters='pyscss', output='gen/scss.css')
all_css = Bundle('vendor/*.css', scss, filters='cssmin', output="gen/all.css")
assets.register('css_all', all_css)

js = Bundle(
  'vendor/jquery.min.js',
  'vendor/jquery.timeago.js',
  'vendor/bootstrap.min.js',
  'javascripts/*.js',
  filters='jsmin', output='gen/packed.js'
)
assets.register('js_all', js)

# constants
SHOWCASE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/static/showcase"
NOTEBOOK_DIR = os.path.dirname(os.path.realpath(__file__)) + "/static/notebooks"
DEMO_DIR= os.path.dirname(os.path.realpath(__file__)) + "/../shogun-demo"
SHOGUN_IRCLOGS = "/home/sonne/shogun/"


# if dev environment
if(os.environ.get('DEV', None)):
  import pdb
  app.config.update(DEBUG = True)
  DEMO_DIR= os.path.dirname(os.path.realpath(__file__)) + "/static/demos"
  SHOGUN_IRCLOGS = os.path.dirname(os.path.realpath(__file__)) + '/static/irclogs'


@app.route('/')
def index():
  notebooks = get_notebooks()
  demos = get_demos()
  all_entries = notebooks + demos

  # group notebooks and demos in sets of 4 for the bottom carousel
  examples = []
  for i in xrange(0,len(all_entries),4):
    examples.append(all_entries[i:(i+4)])

  return render_template('home.html', examples=examples)


@app.route('/gallery')
def gallery():
  notebooks = get_notebooks()
  demos = get_demos()
  examples = notebooks + demos

  return render_template('gallery.html', examples=examples)

@app.route('/examples')
def examples():
  return redirect('http://shogun.ml/cookbook/latest/')

@app.route('/docs')
def docs():
  return redirect('https://github.com/shogun-toolbox/shogun/wiki')

@app.route('/irclogs')
def irclogs():
  logfiles = [ f.replace('#shogun.','').replace('.log.html','') for f in os.listdir(SHOGUN_IRCLOGS) if f.startswith('#shogun') ]
  logfiles.sort()

  logfiles = get_calendar_irc_logs(logfiles)

  return render_template('irclogs.html', logs=logfiles)


@app.route('/irclog/<date>/')
def irclog(date):
  logfile = '%s/#shogun.%s.log.html'  % (SHOGUN_IRCLOGS, date)
  html = open(logfile).read()
  soup = BeautifulSoup(html)
  log = str(soup.body.table)
  return render_template('irclogs.html', log=log)


@app.route('/shogun_readme')
def shogun_readme():
  github = Github()
  md_content = get_github_file('https://raw.githubusercontent.com/shogun-toolbox/shogun/develop/README.md')
  html_content = github.render_markdown(md_content)
  return render_template('external_page.html', title="Shogun Readme", body=html_content)


# utils
def get_notebooks():
  notebooks = []
  for file in os.listdir(NOTEBOOK_DIR):
    if file.endswith(".html"):
      notebook_url = "/static/notebooks/"+file
      notebook_image = notebook_url[:-5]+'.png'
      notebook_title = file[0:-5].replace('_', ' ')

      notebooks.append([notebook_url, notebook_image, notebook_title])

  return notebooks


def get_demos():
  demos = []
  for base, dirs, files in os.walk(DEMO_DIR, topdown=True):
    for name in [ os.path.join(DEMO_DIR, base, f) for f in files if f.endswith(".desc") ]:
      demo_url = 'http://demos.shogun-toolbox.org/' + '/'.join(name.split('/')[-2:])[:-5]
      demo_image = '/static/demos/' + '_'.join(name.split('/')[-2:])[:-5] + '.png'
      demo_title = ' '.join(name.split('/')[-2:])[:-5].replace('_', ' ')

      demos.append([demo_url, demo_image, demo_title])

  return demos


# make sure to use the 'raw' file url
def get_github_file(url):
  request = urllib2.Request(url)

  try:
    response = urllib2.urlopen(request)
    return response.read().decode('utf-8')
  except urllib2.HTTPError, e:
    print e


def get_calendar_irc_logs(logfiles):
  logfiles_set=set(logfiles)
  cal = calendar.Calendar()
  start_entry=logfiles[0]
  end_entry=logfiles[-1]
  start_year=int(start_entry[:4])
  start_month=int(start_entry[5:7])
  end_year=int(end_entry[:4])
  end_month=int(end_entry[5:7])

  all_entries=[]
  for year in xrange(start_year,end_year+1):
    cur_start_month=1
    cur_end_month=12

    if year == start_year:
      cur_start_month=start_month
    if year == end_year:
      cur_end_month=end_month

    year_entries=[]
    for month in xrange(cur_start_month, cur_end_month+1):
      month_entries=[]

      weeks_entries=[]
      week_entries=[]
      weekday=0
      for day in cal.itermonthdays(year, month):
        weekday+=1
        entry=["","", ""]
        if day>0:
          key='%04d-%02d-%02d' % (year,month,day)
          entry=[day, "", ""]
          if key in logfiles_set:
            entry[1:3]=key, os.path.getsize(SHOGUN_IRCLOGS + '/' + '#shogun.%s.log.html' % key)/1024
        week_entries.append(entry)
        if (weekday>0) and (weekday % 7 == 0):
          weeks_entries.append(week_entries)
          week_entries=[]

      if len(week_entries)>0:
        weeks_entries.append(week_entries)
      month_entries=[weeks_entries]
      year_entries.append((calendar.month_name[month], month_entries))
    all_entries.append((year, year_entries[::-1]))

  return all_entries[::-1]


# launch
if __name__ == '__main__':
    app.run()
