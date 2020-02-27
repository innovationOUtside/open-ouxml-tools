# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.3.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # OpenLearn XML Scraper
#
# OU OpenLearn materials are published in a source XML form, which allows some degree of structured access to the document contents.
#
# For example, we can construct a database of images used across OpenLearn unit material, or a list of quotes, or a list of activities.
#
# This notebook is a very first pass, just scraping images, and not adding as much metadata to the table (eg parent course) as it should. As and when I get time to tinker, I'll work on this... ;-)

# + tags=["active-ipynb"]
# %load_ext autoreload
# %autoreload 2
# -

# ## Import some stuff...

# +
import requests

from urllib.parse import urlsplit, urlunsplit
import unicodedata
from lxml import etree

import os


# + tags=["active-ipynb"]
# import requests_cache
# requests_cache.install_cache('openlearn_cache')
#
# -

# ## XML Parser
#
# Routines for parsing the OU XML.

# +
# http://www.open.edu/openlearn/ocw/pluginfile.php/100160/mod_oucontent/oucontent/859/dd203_1_001i.jpg
# http://www.open.edu/openlearn/ocw/pluginfile.php/100160/mod_oucontent/oucontent/859/0c10275d/2c1a8d77/dd203_1_001i.jpg

# +
import moodlescraper as mscpr

# test needs to be be the XML link... need to derive this..
dbname = "molecularworld.db"

# !rm $dbname
# test='https://www.open.edu/openlearn/people-politics-law/politics-policy-people/sociology/the-politics-devolution/content-section-0'
test = "https://www.open.edu/openlearn/science-maths-technology/learn-code-data-analysis/content-section-overview-0"
test = "https://www.open.edu/openlearn/science-maths-technology/computing-ict/discovering-computer-networks-hands-on-the-open-networking-lab/content-section-overview?active-tab=description-tab"
test = "https://www.open.edu/openlearn/science-maths-technology/chemistry/the-molecular-world/content-section-1.1"


mscpr.scrape_unit_openlearn_base(possible_sc_links=[test], dbname=dbname)


# +
import sqlite3
from sqlite_utils import Database
import pandas as pd


conn = sqlite3.connect(dbname, timeout=10)
cursor = conn.cursor()

DB = Database(conn)
display(DB.table_names())
pd.read_sql("SELECT * FROM imagetest LIMIT 3", DB.conn)
pd.read_sql("SELECT * FROM xmlfigures  LIMIT 3", DB.conn)
# pd.read_sql('SELECT srcurl FROM xmlfigures  LIMIT 3',DB.conn)['srcurl'].to_list()
# pd.read_sql('SELECT * FROM xmlfigures LIMIT 3',DB.conn).iloc[0]['imgurl']
# -

pd.read_sql('SELECT * FROM xmlfigures WHERE stub LIKE "%s205_2_i018i%"', DB.conn)

# ## Grab Unit Locations
#
# OpenLearn publish an OPML feed of units. It used to be hierarchical, grouping unitis in to topics, now it seems to be flat with links to units as well as topic feeds. At some point, I'll grab the topic feeds and use it to generate lookup tables from topics to units.

import requests


def getUnitLocations(q="", goforit=False):
    # The OPML file lists all OpenLearn units by topic area
    srcUrl = "http://openlearn.open.ac.uk/rss/file.php/stdfeed/1/full_opml.xml"
    r = requests.get("http://openlearn.open.ac.uk/rss/file.php/stdfeed/1/full_opml.xml")
    rawxml = r.content
    root = etree.fromstring(rawxml)
    # tree = etree.parse(srcUrl)
    # root = tree.getroot()
    items = root.findall(".//body/outline")
    # Handle each topic area separately?
    # The OPML is linear and mixes links to content twith links to topic feeds
    # Need to harvest by topic?
    units = []
    for item in items:
        unit = {}
        tt = item.get("text")
        # print( tt)
        it = item.get("text")
        unit = {"fullname": it}
        if it.startswith("Unit content for"):
            it = it.replace("Unit content for", "")
            url = item.get("htmlUrl")
            rssurl = item.get("xmlUrl")
            unit["url"] = url
            unit["rssurl"] = rssurl
            unit["name"] = it
            # print(url)
            xmlurl = url.replace("content-section-0", "altformat-ouxml")
            # print(xmlurl)
            if goforit:
                c = requests.get(xmlurl)
                _xml_figures(c.content)
        units.append(unit)

    if q:
        units = [unit for unit in units if q in unit["name"]]
    return units


# droptable('xmlfigures')
getUnitLocations()


[i for i in mscpr.getUnitLocations() if i["xmlurl"]][:3]

# ## TO DO
#
# There are other things we can scrape data about as well as images:
#
# - quotes (`<Quote>...</Quote>`)
# - activities (`<Activity><Heading></Heading><Timing><Hours></Hours><Minutes></Minutes></Timing><Question></Question><Discussion></Discussion></Activity>`)
# - box (`<Box><Heading></Heading> ...<SourceReference></SourceReference></Box>`)
# - OU coursecode and title (`<CourseCode></CourseCode>` and `<CourseTitle></CourseTitle>`)
# - identifying references is unstructed in some units, structured in others (`<BackMatter><References><Reference></Reference></References></BackMatter>`)

# ## Example Query

# +
import pandas as pd

import sqlite3

conn = sqlite3.connect("openlearn.sqlite")

pd.read_sql("SELECT * FROM xmlfigures LIMIT 3", conn)
# -

# ## Tidy Up
