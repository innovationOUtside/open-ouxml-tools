# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
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

# moodlescraper.py

# Routines for scraping content from OU Moodle VLE and OpenLearn sites

import time
import random
import requests
import mechanicalsoup
from bs4 import BeautifulSoup
from lxml import etree
import unicodedata
import base64
import os


import pandas as pd

from sqlite_utils import Database


# Need to package this...
from ouxml.vlescrapertools import get_possible_sc_links


# Need to do this a better way; hack for now
DB = None


# Utils

# ===
# via http://stackoverflow.com/questions/5757201/help-or-advice-me-get-started-with-lxml/5899005#5899005
def flatten(el):
    """Utility function for flattening XML tags."""
    if el is None:
        return ""  # Originally returned None; any side effects of move to ''?
    result = [(el.text or "")]
    for sel in el:
        result.append(flatten(sel))
        result.append(sel.tail or "")
    return unicodedata.normalize("NFKD", "".join(result)) or " "


# We use a session just to simplify things wrt VLE scraper
# We could just use requests for the OpenLearn calls
def getSession():
    """Create a connection session to OpenLearn."""

    URL = "https://www.open.edu/openlearn/"

    browser = mechanicalsoup.StatefulBrowser()
    browser.open(URL)
    return browser


def _get_page(url, s=None):
    """
    Utility function to play nice when scraping.
    This will also fetch a page according to a session or a simple get.
    """

    if not url:
        # What's a proper null requests object?
        return None
    # Play nice
    time.sleep(random.uniform(0.1, 0.3))
    if not s or isinstance(s, str):
        r = requests.get(url)
    else:
        # should check this is a valid session
        try:
            r = s.open(url)
        except:
            return None
    return r


# ===


def setup_DB(dbname="test_vle_course_scraper_db.db", newdb=False):
    """Create a new database and database connection."""

    # Need to find a better way to do this
    global DB

    # At the moment this doesn't create a new database
    # if the db already exists we just reuse it.
    # If we are reusing a database, we should upsert not insert,
    # but this also means we need to identify primary keys in tables?

    # Should really find a way to require a confirmation for this?
    if newdb and os.path.isfile(dbname):
        print("Deleting old database: {}", dbname)
        os.remove(dbname)

    print("Creating database connection: {}".format(dbname))
    DB = Database(dbname)

    return DB


def get_full_html_page_url(html_page_url):
    """The printable page is the full page."""
    if "?" in html_page_url:
        plink = "{}&printable=1".format(html_page_url)
    else:
        plink = "{}?printable=1".format(html_page_url)
    return plink


def get_sc_page(html_url, s=None):
    """Try to load a structured content page."""
    # html_page = _get_page('https://learn2.open.ac.uk/mod/repeatactivity/view.php?id=1349903&specialpage=1', s)
    html_page = _get_page(html_url, s)
    if not html_page:
        return None, None, None, None

    # print(html_page.url)
    if "?" in html_page.url:
        sc_link = "{}&content=scxml".format(html_page.url)
    else:
        sc_link = "{}?content=scxml".format(html_page.url)
    sc = _get_page(sc_link, s)

    try:
        raw = sc.content.decode("utf-8")
    except:
        return None, None, None, None

    # if it's an XML page we get
    typ = None
    if raw.startswith("<?xml"):
        typ = "XML"
    elif raw.startswith("<!DOCTYPE html"):
        typ = "HTML"

    # Get the full html_page
    full_html_url = get_full_html_page_url(html_page.url)
    full_html = _get_page(full_html_url, s)

    return typ, html_page.url, raw, full_html.content.decode("utf-8")


def html_xml_save(
    s=None, possible_sc_link=None, table="htmlxml", course_presentation=None
):
    """Save the HTML and XML for a VLE page page."""

    if not possible_sc_link:
        # should really raise error here
        print("need a link")

    if not s:
        if "learn2.open.ac.uk" in possible_sc_link:
            from vlescrapertools import getAuthedSession

            s = getAuthedSession()
        else:
            s = possible_sc_link

    typ, html_page_url, rawxml, html_src = get_sc_page(possible_sc_link, s)

    if typ:
        dbrowdict = {
            "possible_sc_link": possible_sc_link,
            "doctype": typ,
            "html_url": html_page_url,
            "xml": rawxml,
            "html_src": html_src,
            "course_presentation": course_presentation,
            "courseCode": "",
            "courseTitle": "",
            "itemTitle": "",
        }
    else:
        dbrowdict = {}

    # Get some metadata from the XML
    # Item/CourseCode
    # Item/CourseTitle
    # Item/ItemTitle
    if typ == "XML":
        root = etree.fromstring(rawxml.encode("utf-8"))
        # If the course code is contaminated by a presentation suffix, get rid of the presentation code
        dbrowdict["courseCode"] = flatten(root.find("CourseCode")).split("-")[0]
        dbrowdict["courseTitle"] = flatten(root.find("CourseTitle"))
        dbrowdict["itemTitle"] = flatten(root.find("ItemTitle"))

    if dbrowdict:
        DB[table].insert(dbrowdict)

    return typ, html_page_url, rawxml, html_src


def _course_code(xml_content):
    """Get course code from XML."""
    root = etree.fromstring(xml_content)
    return flatten(root.find(".//CourseCode"))


def _xml_figures(xml_content, coursecode="", pageurl=""):
    """Extract figure elements and paths from XML."""
    figdicts = []

    try:
        root = etree.fromstring(xml_content.encode("utf-8"))
    except:
        return False
    figures = (
        root.findall(".//Figure")
        + root.findall(".//InlineFigure")
        + root.findall(".//InlineEquation")
        + root.findall(".//Equation")
    )
    # ??Note that acknowledgements to figures are provided at the end of the XML file with only informal free text/figure number identifers available for associating a particular acknowledgement/copyright assignment with a given image. It would be so much neater if this could be bundled up with the figure itself, or if the figure and the acknowledgement could share the same unique identifier?
    figdict = {}

    for figure in figures:
        figdict = {
            "xpageurl": pageurl,
            "caption": "",
            "src": "",
            "coursecode": coursecode,
            "desc": "",
            "owner": "",
            "item": "",
            "itemack": "",
        }
        img = figure.find("Image")

        # Is there a way I can actually generate a behind the firewall at least URL for embedding actual images?
        if img is None:
            continue

        figdict["xurl"] = img.get("src")

        if figdict["xurl"] is None:
            continue

        xsrc = img.get("x_imagesrc")
        figdict["caption"] = flatten(figure.find("Caption")).strip()
        figdict["alt"] = flatten(figure.find("Alternative")).strip()
        figdict["alt"] = (
            figdict["alt"] if figdict["alt"] else "Figure"
        )  #  should really set this to Figure | InlineEquation etc
        # in desc, need to find a way of stripping <Number> element from start of description
        figdict["desc"] = flatten(figure.find("Description"))
        # <SourceReference><ItemRights><OwnerRef/><ItemRef/><ItemAcknowledgement/></ItemRights></SourceReference>
        ref = figure.find("SourceReference")
        if ref is not None:
            rights = ref.find("ItemRights")
            if rights is not None:
                figdict["owner"] = flatten(rights.find("ItemRights"))
                figdict["item"] = flatten(rights.find("ItemRights"))
                figdict["itemack"] = flatten(rights.find("ItemAcknowledgement"))
        # print( 'figures',xsrc,caption,desc,src)
        # The following tries to hack around things like \t appearing in the path
        figdict["stub"] = (
            str(figdict["xurl"].encode("utf-8")).split("\\")[-1].strip("'")
        )
        figdict["stub"] = figdict["stub"].split("/")[-1]
        # print('xmlstub...',figdict['stub'])
        figdict["minstub"] = figdict["stub"].split(".")[0]
        figdicts.append(figdict)
    table = "xmlfigures"
    if figdicts:
        DB[table].insert_all(figdicts)
    return figdicts


# +
# TO DO - for some reason we are getting duplicate rows on images?
from urllib.parse import urlsplit, urlunsplit


def _xml_figures_openlearn(xml_content, coursecode="", pageurl="", root=None):
    """Identify image elements and paths in OpenLearn XML."""
    figdicts = []
    if root is None or not len(root):
        try:
            root = etree.fromstring(xml_content)
        except:
            return False
    figures = []
    for t in ["Figure", "InlineFigure", "Equation", "InlineEquation"]:
        figures = figures + root.findall(".//{}".format(t))
    # ??Note that acknowledgements to figures are provided at the end of the XML file with only informal free text/figure number identifers available for associating a particular acknowledgement/copyright assignment with a given image. It would be so much neater if this could be bundled up with the figure itself, or if the figure and the acknowledgement could share the same unique identifier?
    figdict = {}
    print("XML figures list len:", len(figures))
    for figure in figures:
        figdict = {
            "xpageurl": pageurl,
            "caption": "",
            "src": "",
            "coursecode": coursecode,
            "desc": "",
            "owner": "",
            "item": "",
            "itemack": "",
        }
        img = figure.find("Image")
        # The image url as given does not resolve - we need to add in provided hash info
        figdict["srcurl"] = img.get("src")
        xsrc = img.get("x_imagesrc")
        if figdict["srcurl"] is None:
            continue

        figdict["x_folderhash"] = img.get("x_folderhash")
        figdict["x_contenthash"] = img.get("x_contenthash")
        if (
            figdict["x_contenthash"] is not None
            and figdict["x_contenthash"] is not None
        ):
            path = urlsplit(figdict["srcurl"])
            sp = path.path.split("/")
            path = path._replace(
                path="/".join(
                    sp[:-1]
                    + [figdict["x_folderhash"], figdict["x_contenthash"]]
                    + [xsrc]  # sp[-1:]
                )
            )
            figdict["imgurl"] = urlunsplit(path)
        else:
            figdict["imgurl"] = ""

        figdict["caption"] = flatten(figure.find("Caption")).strip()
        figdict["alt"] = flatten(figure.find("Alternative")).strip()
        figdict["alt"] = (
            figdict["alt"] if figdict["alt"] else "Figure"
        )  #  should really set this to Figure | InlineEquation etc

        # in desc, need to find a way of stripping <Number> element from start of description
        figdict["desc"] = flatten(figure.find("Description"))
        # <SourceReference><ItemRights><OwnerRef/><ItemRef/><ItemAcknowledgement/></ItemRights></SourceReference>
        ref = figure.find("SourceReference")
        if ref is not None:
            rights = ref.find("ItemRights")
            if rights is not None:
                figdict["owner"] = flatten(rights.find("ItemRights"))
                figdict["item"] = flatten(rights.find("ItemRights"))
                figdict["itemack"] = flatten(rights.find("ItemAcknowledgement"))
        # print( 'figures',xsrc,caption,desc,src)

        figdict["stub"] = figdict["srcurl"].split("/")[-1]
        # print('xmlstub...',figdict['stub'])
        figdict["minstub"] = figdict["stub"].split(".")[0]

        figdicts.append(figdict)

    table = "xmlfigures"
    if figdicts:
        DB[table].insert_all(figdicts)

        # We can also get the actual images from the imgurl location
        saveImages(figdicts, imgurlkey="imgurl")

    return figdicts


def _xml_glossary(xml_content, coursecode="", pageurl=""):
    """Extract glossary items and add to db table."""

    try:
        root = etree.fromstring(xml_content)
    except:
        return False

    glossdicts = []
    # TO DO
    gloss = root.findall(".//{}".format("??? TO DO "))
    table = "xmlglossary"
    if glossdicts:
        DB[table].insert_all(glossdicts)


# -

# requires the session
def get_as_base64(url, s=None):
    """Get data as base64 encoded data."""
    data = _get_page(url, s).content

    return base64.b64encode(data), data


def saveImages(_figures_list, s=None, imagetable="imagetest", imgurlkey="hurl"):
    """Save images into database."""

    if not imagetable:
        imagetable = "imagetest"

    # print("Saving images into database...")
    imagedicts = []
    imgkeys = []
    # print('figures list',_figures_list)
    for _figure in _figures_list:
        b64image, d = get_as_base64(_figure[imgurlkey], s)
        # with open(t['stub'], 'wb') as f:
        #    f.write(d)

        imagedict = {
            "b64image": b64image,
            "stub": _figure["stub"],
            "minstub": _figure["minstub"],
        }
        if imagedict["stub"] not in imgkeys:
            imgkeys.append(imagedict["stub"])
            imagedicts.append(imagedict)

    if imagedicts:
        DB[imagetable].insert_all(imagedicts)


# The HTML figures should be pulled from the full HTML page
def _html_figures(
    html_content, s=None, coursecode="", pageurl="", imagetable="imagetest"
):
    """Extract images from HTML page."""
    # display('make html soup')
    soup = BeautifulSoup(html_content, "lxml")
    # result = etree.tostring(html, pretty_print=True, method="html")
    # display('look for html images')
    figures = soup.find_all("img")
    figdicts = []
    # display('html figures - count:', len(figures))
    # ??Note that acknowledgements to figures are provided at the end of the XML file with only informal free text/figure number identifers available for associating a particular acknowledgement/copyright assignment with a given image. It would be so much neater if this could be bundled up with the figure itself, or if the figure and the acknowledgement could share the same unique identifier?
    i = 0
    for figure in figures:
        # print(i)
        i = i + 1
        figdict = {
            "hurl": "",
            "hpageurl": pageurl,
            "stub": "",
            "coursecode": coursecode,
        }
        # Is there a way I can actually generate a behind the firewall at least URL for embedding actual images?
        figdict["hurl"] = figure.get("src")
        # xsrc=img.get('x_imagesrc')
        # caption=flatten(figure.find('Caption'))
        # in desc, need to find a way of stripping <Number> element from start of description
        # desc=flatten(figure.find('Description'))
        # print( 'figures',src)
        figdict["stub"] = figdict["hurl"].split("/")[-1]
        figdict["minstub"] = figdict["stub"].split(".")[0]
        # Some hacky guesses about whether it's a meaningful image
        # Probably need to go back and check these to see if there is anything useful there
        # if 'mod_oucontent' in figdict['hurl'] and 'osep' not in  figdict['hurl']:
        if "mod_oucontent" in figdict["hurl"]:
            figdicts.append(figdict)
        # scraperwiki.sqlite.save(unique_keys=[],table_name='htmlfigures',data=figdict)
        # scraperwiki.sqlite.save(unique_keys=[],table_name='figures',data={'ccu':courseCode,'src':src,'xsrc':xsrc,'caption':caption,'desc':desc,'ccid':courseID,'xid':xID,'slug':slug})
    table = "htmlfigures"
    # print('figdicts',figdicts)
    if figdicts:
        DB[table].insert_all(figdicts)

    # print(', '.join([f['minstub'] for f in figdicts]))

    saveImages(figdicts, s, imagetable=imagetable)

    return figdicts


# +
# Page grabbers for OpenLearn content
def get_openlearn_sc_page(html_url, s=None, xml_url=None):
    """Try to load a structured content page."""
    # html_page = _get_page('https://learn2.open.ac.uk/mod/repeatactivity/view.php?id=1349903&specialpage=1', s)

    if "content-section" not in html_url:
        print("I don't think I can work with that HTML URL...")
        return None, None, None, None

    html_page = _get_page(html_url, s)
    if not html_page:
        return None, None, None, None

    # print(html_page.url)
    html_page_url_stub = html_url.split("/content-section")[0]
    if xml_url is None:
        sc_link = "{}/altformat-ouxml".format(html_page_url_stub)
    else:
        sc_link = xml_url

    sc = _get_page(sc_link, s)

    try:
        print("Decoding utf-8...")
        raw = sc.content.decode("utf-8")
        print("...done decoding utf-8")
    except:
        return None, None, None, None

    # if it's an XML page we get
    typ = None
    if raw.startswith("<?xml"):
        typ = "XML"
    elif raw.startswith("<!DOCTYPE html"):
        typ = "HTML"

    # Get the full html_page
    # For OpenLearn, do we really need to do this?
    print("Getting full html...")
    full_html_url = "{}/altformat-html".format(html_page_url_stub)
    full_html = _get_page(full_html_url, s)
    print("...done getting full html")
    
    return typ, html_page_url_stub, raw, full_html.content  # .decode("utf-8")


def html_xml_save_openlearn(
    s=None, possible_sc_link=None, table="htmlxml", course_presentation=None
):
    """Save HTML and XML from an OpenLearn OU-XML document URL."""

    if not possible_sc_link:
        # should really raise error here
        print("need a link")

    if not s:
        s = getSession()

    print("getting ou-xml")
    typ, html_page_url, rawxml, html_src = get_openlearn_sc_page(possible_sc_link, s)

    if typ:
        dbrowdict = {
            "possible_sc_link": possible_sc_link,
            "doctype": typ,
            "html_url": html_page_url,
            "xml": rawxml,  #'html_src': html_src,
            "course_presentation": course_presentation,
            "courseCode": "",
            "courseTitle": "",
            "itemTitle": "",
        }
    else:
        dbrowdict = {}

    # Get some metadata from the XML
    # Item/CourseCode
    # Item/CourseTitle
    # Item/ItemTitle
    if typ == "XML":
        print("parsing XML...")
        root = etree.fromstring(rawxml.encode("utf-8"))
        # If the course code is contaminated by a presentation suffix, get rid of the presentation code
        dbrowdict["courseCode"] = flatten(root.find("CourseCode")).split("-")[0]
        dbrowdict["courseTitle"] = flatten(root.find("CourseTitle"))
        dbrowdict["itemTitle"] = flatten(root.find("ItemTitle"))
        print("...done parsing XML")
    else:
        root = None

    if dbrowdict:
        print("saving xml into db...")
        DB[table].insert(dbrowdict)
        print("...done saving xml into db")

    return typ, html_page_url, rawxml, html_src, root


def scrape_unit_openlearn_base(
    s=None,
    possible_sc_links=None,
    coursecode="",
    imagetable="imagetest",
    course_presentation="unknown",
    dbname=None,
    newdb=False,
):
    """Scrape an OpenLearn unit homepage for OU-XML link."""
    # OpenLearn is easier because we can derive the image URL from the XML
    # OpenLearn has different pattern on creating the XML URL but html_xml_save should work - scxml is good?
    # Test that we can get a content0 page
    # TO DO - ideally, we should be able to cope with *any* OpenLEarn unit page
    # Get the XML
    # Parse the figures: _xml_figures_openlearn() does this
    # Save the figures

    if dbname:
        setup_DB(dbname, newdb=newdb)
    elif not DB:
        # Or should we just set up an in memory db?
        setup_DB("dummydb.db")

    for possible_sc_link in possible_sc_links:
        typ, html_page_url, rawxml, html_src, root = html_xml_save_openlearn(
            s, possible_sc_link, course_presentation=course_presentation
        )
        print(typ)
        if typ == "XML":
            print("trying images")
            print("going into _xml_figures_openlearn")
            _xml_figures_openlearn(
                rawxml.encode("utf-8"),
                coursecode=coursecode,
                pageurl=html_page_url,
                root=root,
            )
            # Sometimes we can get a path to the image from the XML? Always for OpenLearn in Image[@src]?
            # Instead will have to fill the gaps in from the HTML.
            # So maybe we should just get the images from the html anyway?
            # saveImages(figdicts, s, imagetable=imagetable, imgurlkey='imgurl')

            # TO DO - not convinced about the HTML..
            # Can we get by with just the xml?

            # print('going into _html_figures_openlearn')
            # _html_figures( html_src, s, coursecode=coursecode,
            #              pageurl=html_page_url, imagetable=imagetable)

            # Get glossary items
            # _xml_glossary(rawxml.encode("utf-8"),
            #                       coursecode=coursecode, pageurl=html_page_url)

            # Get Learning Objectives
            # _xml_lo(rawxml.encode("utf-8"),
            #                       coursecode=coursecode, pageurl=html_page_url)


# -


def _preflight(s=None, course_presentation=None, dbname=None, newdb=True):
    """Abstract out set up elements for new scrapes."""

    if not s:
        from vlescrapertools import getAuthedSession

        s = getAuthedSession()

    if not dbname and newdb:
        dbname = "auto_{}".format(course_presentation.replace("-", "_"))
        print("Setting up new db: {}".format(dbname))
        setup_DB("{}.db".format(dbname))
    elif dbname:
        setup_DB(dbname)

    return s


def scrape_course_base(
    s=None,
    possible_sc_links=None,
    coursecode="",
    imagetable="imagetest",
    course_presentation="unknown",
    dbname=None,
    newdb=False,
):
    """ Scrape a course... Or try to..."""

    if dbname:
        setup_DB(dbname, newdb=newdb)
    elif not dbname:
        # Or should we just set up an in memory db?
        setup_DB("dummydb.db")

    for possible_sc_link in possible_sc_links:

        typ, html_page_url, rawxml, html_src = html_xml_save(
            s, possible_sc_link, course_presentation=course_presentation
        )

        if not typ:
            continue
        # print('Trying to save images...')
        # The images should also be saved with module presentation info?
        _xml_figures(rawxml, coursecode=coursecode, pageurl=html_page_url)
        _html_figures(
            html_src,
            s,
            coursecode=coursecode,
            pageurl=html_page_url,
            imagetable=imagetable,
        )


def scrape_provided_links(
    s=None, provided_links=None, course_presentation=None, dbname=None
):
    """Scrape provided possible structured content links."""

    if not provided_links or not course_presentation:
        print(
            """You MUST provide a module-presentation code, 
                 for example: TM351-18J, and a list of links to scrape\n"""
        )
        return None

    s = _preflight(s, course_presentation, dbname)

    COURSE_CODE = course_presentation.split("-")[0]
    scrape_course_base(
        s,
        possible_sc_links=provided_links,
        coursecode=COURSE_CODE,
        course_presentation=course_presentation,
    )


def scrape_course_presentation(
    s=None, course_presentation=None, dbname=None, view_pages_only=False
):
    """Scrape the VLE for a particular presentation of a particular module."""

    # Need to do this a better way; hack for now
    # global DB

    # should really check the format of course_presentation to check it's valid?
    if not course_presentation:
        print("You MUST provide a module-presentation code, for example: TM351-18J\n")
        return

    s = _preflight(s, course_presentation, dbname)

    possible_sc_links = get_possible_sc_links(s, course_presentation)

    if view_pages_only:
        possible_sc_links = [psc for psc in possible_sc_links if "/view.php?" in psc]

    COURSE_CODE = course_presentation.split("-")[0]
    scrape_course_base(
        s,
        possible_sc_links=possible_sc_links,
        coursecode=COURSE_CODE,
        course_presentation=course_presentation,
    )


# OpenLearn tools
def getUnitLocations(q="", goforit=False):
    """Get URLs and unit names for OpenLearn units."""
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
        it = item.get("text")
        unit = {"fullname": it}
        if it.startswith("Unit content for"):
            it = it.replace("Unit content for", "")
            url = item.get("htmlUrl")
            rssurl = item.get("xmlUrl")
            unit["url"] = url
            unit["srcurl"] = rssurl
            unit["name"] = it
            # print(url)
            xmlurl = url.replace("content-section-0", "altformat-ouxml")
            # print(xmlurl)
            if goforit:
                c = requests.get(xmlurl)
                _xml_figures(c.content)
        units.append(unit)

    if q:
        units = [
            unit
            for unit in units
            if "name" in unit
            and all(word in unit["name"].lower() for word in q.lower().split())
        ]
    return units
