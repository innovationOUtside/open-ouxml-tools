# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.2.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# vlescrapertools.py

# Tools to support the scraping of the OU Moodle VLE

import time
import random
import mechanicalsoup
from bs4 import BeautifulSoup

# This is not used at the moment?
def _html_title(html_content):
    """ Get the title of an HTML page. """

    soup = BeautifulSoup(html_content, "lxml")
    return soup.find("title").text.split("-")[0]


def _get_page(s, url):
    """ Utility function to play nice when scraping. """

    # Play nice
    time.sleep(random.uniform(0.1, 0.3))

    r = s.open(url)
    return r


def _search_by_code(s, code=None, service="learn2"):
    """ Search VLE for modules with a particular module code. """

    if not code:
        code = input("Module code (e.g. TM129 or TM129-17J): ")

    surl = "https://{}.open.ac.uk/course/search.php?search={}".format(service, code)
    search = _get_page(s, surl)
    soup = BeautifulSoup(search.content, "lxml")
    links = [h3.find_next("a") for h3 in soup.find_all("h3", {"class": "coursename"})]
    module_links = []
    for link in links:
        if link.get("href"):
            # https://stackoverflow.com/a/22497114/454773
            for link_txt in link.findAll("span"):
                link_txt.unwrap()
                module_links.append((link.text, link.get("href")))
    return module_links


def _search_focus(s, code=None):
    """ Search for a particular module / presentation.
        The search should return only a single item. """

    if not code:
        code = input("Module code (e.g. TM129-17J): ")

    results = _search_by_code(s, code)
    if not len(results):
        print('Nothing found for "{}"'.format(code))
    elif len(results) > 1:
        print(
            "Please be more specific:\n\t{}\n".format(
                "\n\t".join([r[0].split(" ")[0] for r in results])
            )
        )
    else:
        return results[0]
    return (None, None)


# +
from collections import OrderedDict


def _get_potential_sc_links(soup, optimise=True):
    """Scan links on a page for possible structured content links."""

    probablynots = [
        "area=assessment",
        "/mod/quiz/",
        "/mod/oustudyplansubpage/",
        "mod/forumng",
        "oustudyplan",
    ]
    # Resource downloads / zipfiles etc https://learn2.open.ac.uk/course/format/oustudyplan/resource.php?id=1521825&repeat=1

    links = soup.findAll("a")
    sclinks = []
    for link in links:
        # print(link.get('href'))
        if link.get("href"):
            href = link.get("href")
            if optimise:
                # if 'view.php?id=' in href and "area=assessment" not in href and '/mod/quiz/' not in href and '/mod/oustudyplansubpage/' not in href:
                if "view.php?id=" in href and not any(
                    pn in href for pn in probablynots
                ):
                    sclinks.append(link.get("href"))
                elif "repeatactivity/original.php" in href:
                    # Can these be valid OU-XML pages? Example? I've seen PDFs on this?
                    sclinks.append(link.get("href"))
            else:
                sclinks.append(link.get("href"))

    # Remove suffix #etc; dedupe via list(set())
    # sclinks = list(set([sclink.split('#')[0] for sclink in sclinks]))
    sclinks = list(OrderedDict.fromkeys(sclinks))

    return sclinks


# -


def _html_sc_links(html_content, optimise=True):
    """ Try to identify page URLs for pages generated from a structured content document. """

    soup = BeautifulSoup(html_content, "lxml")
    calendar = soup.find("ul", {"class": "oustudyplan"})

    return _get_potential_sc_links(calendar)


def get_possible_sc_links(s, code=None):
    """ Get list of links that may point to VLE HTML pages
        derived from OU-XML structured conent documents. 
    """
    (COURSE_NAME, COURSE_URL) = _search_focus(s, code)
    course_home = _get_page(s, COURSE_URL)
    possible_sc_links = _html_sc_links(course_home.content)
    return possible_sc_links


def get_possible_sc_links_from_page(s, pages, sid="", classname=""):
    """ Get list of links that may point to VLE HTML pages
        derived from a target page or pages on the VLE. 
    """

    pages = [pages] if isinstance(pages, str) else pages

    # TO DO - if a section id exists, get the html tag with that id

    if not pages:
        print("No pages to look for links identified?")
        return

    possible_sc_links = []

    for url in pages:
        page = _get_page(s, url)
        soup = BeautifulSoup(page.content, "lxml")

        if classname:
            soup = soup.select_one(".{}".format(classname))

        possible_sc_links = possible_sc_links + _get_potential_sc_links(soup)  #

    possible_sc_links = list(OrderedDict.fromkeys(possible_sc_links))
    return possible_sc_links


def scrape_course_presentation(s=None, course_presentation=None, dbname=None):
    """ Scrape the VLE for a particular presentation of a particular module. """

    # Need to do this a better way; hack for now
    # global DB

    if not s:
        s = getSession()

    # should really check the format of course_presentation to check it's valid?
    if not course_presentation:
        print("You MUST provide a module-presentation code, for example: TM351-18J\n")

    if not dbname and not DB:
        dbname = "auto_{}".format(course_presentation.replace("-", "_"))
        print("Setting up new db: {}".format(dbname))
        setup_DB("{}.db".format(dbname))
    elif not DB:
        setup_DB(dbname)

    possible_sc_links = get_possible_sc_links(
        s, course_presentation, classname="oustudyplan"
    )

    COURSE_CODE = course_presentation.split("-")[0]
    scrape_course_base(
        s,
        possible_sc_links=possible_sc_links,
        coursecode=COURSE_CODE,
        course_presentation=course_presentation,
    )
