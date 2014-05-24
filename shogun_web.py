from flask import Flask, render_template, redirect
from BeautifulSoup import BeautifulSoup
import os
import calendar

import pdb

# initialization
app = Flask(__name__)
app.config.update(
    DEBUG = True,
)

# constants
NOTEBOOK_DIR = os.path.dirname(os.path.realpath(__file__)) + "/static/notebooks"
#DEMO_DIR= os.path.dirname(os.path.realpath(__file__)) + "/../shogun-demo"
DEMO_DIR= os.path.dirname(os.path.realpath(__file__)) + "/static/demos"
#SHOGUN_PLANET='/home/sonne/shogun/planet-index.html'
SHOGUN_PLANET = os.path.dirname(os.path.realpath(__file__)) + '/static/planet-index.html'
#SHOGUN_IRCLOGS = "/home/sonne/shogun/"
SHOGUN_IRCLOGS = os.path.dirname(os.path.realpath(__file__)) + '/static/irclogs'

# controllers
@app.route('/')
def index():
  notebooks = get_notebooks()
  demos = get_demos()
  all_entries = notebooks + demos

  top_carousel = all_entries

  # group notebooks and demos in sets of 4 for the bottom carousel
  bottom_carousel = []
  for i in xrange(0,len(all_entries),4):
    bottom_carousel.append(all_entries[i:(i+4)])

  return render_template('home.html', top_carousel=top_carousel, bottom_carousel=bottom_carousel)


@app.route('/about')
def about():
  return render_template('about.html')


@app.route('/docs')
def docs():
  return redirect('http://www.shogun-toolbox.org/doc/en/current/')


@app.route('/blog')
def planet():
  html=file(SHOGUN_PLANET).read()
  soup = BeautifulSoup(html)
  articles=[]
  for article in soup.body.findAll("div", { "class" : "daygroup" }):
    polished='<dt><h1>' + article.h2.string + '</h1></dt>'
    articles.append(polished + unicode(article.div.div).replace('class="content"',"").replace('{tex}','\[').replace('{/tex}','\]'))

  return render_template('planet.html', articles=articles)


@app.route('/news')
def news():
  return "The News"


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


# utils
def get_notebooks():
  notebooks = []
  for file in os.listdir(NOTEBOOK_DIR):
    if file.endswith(".html"):
      notebook_url = "/static/notebooks/"+file
      notebook_image = notebook_url[:-5]+'.png'
      notebooks.append([notebook_url, notebook_image])

  return notebooks

def get_demos():
  paths = []
  for base, dirs, files in os.walk(DEMO_DIR, topdown=True):
    for name in [ os.path.join(DEMO_DIR, base, f) for f in files if f.endswith(".desc") ]:
      paths.append(('/'.join(name.split('/')[-2:])[:-5]+'/', '_'.join(name.split('/')[-2:])[:-5] + '.png'))

  links=[]
  for path in paths:
    links.append(('http://demos.shogun-toolbox.org/%s' % path[0], '/static/demos/%s' % path[1]))

  return links

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
