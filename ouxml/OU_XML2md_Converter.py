# jupyter nbconvert ouxml/OU_XML2md_Converter.ipynb --to script --template cleaner_py.tpl
# black ouxml/*.py#!/usr/bin/env python
# coding: utf-8


# !pip3 install markdownify
from bs4 import BeautifulSoup
from markdownify import markdownify as md


from pkg_resources import resource_string

xslt = resource_string(__name__, "xslt/ouxml2md.xslt")


import lxml.html
from lxml import etree

xslt_doc = etree.fromstring(xslt)
xslt_transformer = etree.XSLT(xslt_doc)


import pathlib


def checkDirPath(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


# Do some setup
import os

# If it looks like the file is down a directory path, make sure the path is there
# If it isn't, the XSLT won't work when it tries to write the output files...
def check_outdir(output_path_stub):
    path = output_path_stub.split("/")
    if len(path) > 1:
        dirpath = "/".join(path[:-1])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)


import sqlite3
from sqlite_utils import Database


import pandas as pd
from lxml import etree


# TO DO - it would be better if the following accepted an XML string or the path to an XML file
def transform_xml2md(xml, output_path_stub="testout"):
    """Take an OU-XML document as a string 
       and transform the document to one or more markdown files."""

    check_outdir(output_path_stub)

    # with open('xslt/ouxml2md.xslt','r') as f:
    #    xslt_md = f.read()
    xslt_md = xslt
    xslt_doc = etree.fromstring(xslt_md)
    xslt_transformer = etree.XSLT(xslt_doc)

    source_doc = etree.fromstring(xml.encode("utf-8"))

    # It would be handy if we could also retrieve what files the transformer generated?
    # One way of doing this might be to pop everything into a temporary directory
    # and then parse the contents of that directory into a database table?
    output_doc = xslt_transformer(
        source_doc, filestub=etree.XSLT.strparam("{}".format(output_path_stub))
    )


def transformer(conn, key, val, output_path_stub="testout"):

    check_outdir(output_path_stub)

    # key / val is something like url / 1432311 ie a view resource ID
    dummy_xml = pd.read_sql(
        "SELECT * FROM htmlxml WHERE {} LIKE '%{}%'".format(key, val), conn
    )["xml"]
    # If there is more than one XML file returned, just go with the first one for now
    # TO DO - improve this behaviour if multiple files are returned
    dummy_xml = dummy_xml[0]
    transform_xml2md(dummy_xml, output_path_stub=output_path_stub)


import re
import os


def _post_process(output_dir_path):
    # postprocess
    if os.path.exists(output_dir_path):
        for fn in [f for f in os.listdir(output_dir_path) if re.match(".*\.md$", f)]:
            fnp = os.path.join(output_dir_path, fn)
            with open(fnp) as f:
                txt = _txt = f.read()
                # Do postprocess step(s)

                # Get rid of excess end of lines
                txt = re.sub(r"[\r\n][\r\n]{2,}", "\n\n", txt)

                # Get rid of excess end of lines in code blocks
                txt = re.sub(r"```python[\r\n]{2,}", "```python\n", txt)

            # Optionally rewrite the supplied markdown file with re-referenced image links
            if txt != _txt:
                print("Rewriting {}".format(fnp))
                with open(fnp, "w") as f:
                    f.write(txt)


import os


# TO DO - we need a better form of pattern matching and rewriting
# to allow more flexibility in the patterned naming of created directories and renamed files
def _directory_processor(srcdir, new_suffix="part_"):
    """Take filenames of the form stub_WW_NN.md in a flat directory and map them to
       filenames of form the {new_suffix}_WW/stub_WW_NN.md in the same directory."""
    weeks = []
    srcdir = srcdir.rstrip("/")
    for f in os.listdir(srcdir):
        # for example, stub_00_01.md
        w = f.split("_")[1]
        # gives w as 00
        if w not in weeks:
            weeks.append(w)
    for w in weeks:
        newdir = f"{srcdir}/{new_suffix}{w}"
        # for example, testdir/week_00
        if os.path.isdir(newdir):
            print(f"{newdir} already exists...")
        else:
            os.makedirs(newdir)
    for f in os.listdir(srcdir):
        if f.endswith(".md"):
            # For example stub_00_01.md
            w = f.split("_")[1]
            # for example w as 00
            os.rename(f"{srcdir}/{f}", f"{srcdir}/{new_suffix}{w}/{f}")
            # so testdir/stub_00_01.md becomes testdir/week_00/stub_00_01.md


import re
import os


import jupytext


# https://stackoverflow.com/a/29280824/454773
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

# First create the treeprocessor


class ImgExtractor(Treeprocessor):
    def run(self, doc):
        "Find all images and append to markdown.images. "
        self.md.images = []
        for image in doc.findall(".//img"):
            self.md.images.append(image.get("src"))


# Then tell markdown about it


class ImgExtExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        img_ext = ImgExtractor(md)
        md.treeprocessors.add("imgext", img_ext, ">inline")


# Finally create an instance of the Markdown class with the new extension

md = markdown.Markdown(extensions=[ImgExtExtension()])


def get_imgkeys_from_md(md_raw=None, md_filepath=None):
    """Generate imgkeys set for image paths in markdown file."""

    if md_raw is None and md_filepath is not None:
        md_raw = open(md_filepath).read()

    html = md.convert(md_raw)

    # The img URLs may be in one of two forms:

    imgkeys = {}

    # \\\\DCTM_FSS\\content\\Teaching and curriculum\\Modules\\T Modules\\TM112\\TM112 materials\\Block 1 e1\\Block 1 Part 1\\_Assets\\tm112_intro_table_01.eps
    imgkeys.update({u: u.split("\\")[-1] for u in md.images if "\\" in u})

    # https://openuniv.sharepoint.com/sites/tmodules/tm112/block2e1/tm112_blk02_pt04_f07.tif
    imgkeys.update({u: u.split("/")[-1] for u in md.images if "/" in u})

    return imgkeys


def generate_imgdict(imgkeys, DB):
    """Automatically generate an imgdict that maps agains links in a markdown file."""

    q = """
        SELECT DISTINCT xurl, h.stub as p , b64image
        FROM htmlfigures h JOIN xmlfigures x JOIN imagetest i
        WHERE x.minstub=h.minstub 
        AND i.stub=h.stub
        AND x.stub in ({});
        """.format(
        ", ".join(['"{}"'.format(imgkeys[k]) for k in imgkeys])
    )
    tmp_img = pd.read_sql(q, DB.conn)
    imgdict = tmp_img.set_index("xurl").to_dict()["p"]

    # Return the dataframe from which we can save the images to disk
    return tmp_img, imgdict


# OU_Course_Material_Assets.ipynb currently has scraper for getting a database together


import os.path


def _crossmatch_xml_html_links(imgdict, fn, imgdirpath="", rewrite=False):
    """ Try to reconcile XML paths to HTML image paths in supplied markdown file. """

    # Open the markdown file
    with open(fn) as f:
        txt = _txt = f.read()
        # Replace image references with actual image links
        for k in imgdict:
            # print(k.lstrip('\\'))
            txt = txt.replace(
                k.lstrip("\\"), "{}".format(os.path.join(imgdirpath, imgdict[k]))
            )

    # Optionally rewrite the supplied markdown file with re-referenced image links
    if rewrite and (txt != _txt):
        print("Rewriting {}".format(fn))
        with open(fn, "w") as f:
            f.write(txt)

    # Return the rewritten markdown
    return txt


import re


def crossmatch_xml_html_links(
    imgdict, imgdirpath="", contentdir=".", content_prefix=""
):
    """ For markdown files in a content directory, rewrite matched image URLs. """

    # Detect markdown files
    candidate_files = [
        "{}/{}".format(contentdir, f)
        for f in os.listdir(contentdir)
        if re.match(".*\.md$", f)
    ]

    if content_prefix:
        candidate_files = [f for f in candidate_files if f.startswith(content_prefix)]

    for fn in candidate_files:
        print("Handling {}".format(fn))
        _ = _crossmatch_xml_html_links(imgdict, fn, imgdirpath, rewrite=True)
        # We could save the md files to a table here, and perhaps also convert to ipynb in same table?


import base64


def save_image_from_db(x, imgdir="testimages"):
    """ Save image in db to file. """

    img_data = x["b64image"]  # sql("SELECT * FROM imagetest  LIMIT 1;")[0]['b64image']
    fn = "{}/{}".format(imgdir, x["p"])
    with open(fn, "wb") as f:
        f.write(base64.decodebytes(img_data))

    return fn


import os.path


# OpenLearn image map
# For openlearn units, we just have the xml and imagetest tables
# Rewrite imagelinks as stubs
# BUT  - we need some sort of secret for the image file dereferencing to work?
# save images
def openlearn_image_mapper(dbname, _basedir="oumd_demo3", _imgdir="testimages"):
    def _generate_imgdict(DB, imgkeys):
        """Automatically generate an imgdict that maps agains links in a markdown file."""

        q = """
            SELECT DISTINCT srcurl, x.stub as p, b64image
            FROM xmlfigures x JOIN imagetest i
            WHERE x.minstub=i.minstub AND x.minstub in ({});
            """.format(
            ", ".join(['"{}"'.format(imgkeys[k].split('.')[0]) for k in imgkeys])
        )
        tmp_img = pd.read_sql(q, DB.conn)
        imgdict = tmp_img.set_index("srcurl").to_dict()["p"]

        # Return the dataframe from which we can save the images to disk
        return tmp_img, imgdict

    conn = sqlite3.connect(dbname, timeout=10)
    cursor = conn.cursor()

    DB = Database(conn)
    imgdirpath = os.path.join(_basedir, _imgdir)
    checkDirPath(imgdirpath)

    # Should this cope with nested directories and put an image dir in each content dir
    # or one image dir for the whole course?
    imgdict = {}

    # Detect markdown files
    candidate_files = [f for f in os.listdir(_basedir) if re.match(".*\.md$", f)]

    for fn in candidate_files:
        imgkeys = get_imgkeys_from_md(md_filepath="{}/{}".format(_basedir, fn))

        # for each page, get the links
        tmp_img, _imgdict = _generate_imgdict(DB, imgkeys)
        imgdict = {**imgdict, **_imgdict}

        # for each page, save the images
        tmp_img.apply(
            lambda x: save_image_from_db(x, imgdir=os.path.join(_basedir, _imgdir)),
            axis=1,
        )

    # We need to go round again having collected all the image keys
    for fn in candidate_files:
        # Rewrite the links
        print("Handling {}".format(fn))
        _ = _crossmatch_xml_html_links(
            imgdict, os.path.join(_basedir, fn), _imgdir, rewrite=True
        )


def _process_ouxml_doc(row, DB=None, _basedir="", _imgdir=""):
    session = "{}_{}".format(
        "{:02d}".format(row.name), "_".join(row["itemTitle"].split()[:2])
    )
    output_path_dir = os.path.join(_basedir, session)
    output_path_stub = "{}/Section".format(output_path_dir)

    # pages = pd.read_sql('SELECT * FROM htmlxml WHERE course_presentation="TM112-19J" and itemTitle LIKE "%{}%" '.format('Block {} Part {}'.format(block, part)),DB.conn)
    # pages = pd.read_sql('SELECT * FROM htmlxml WHERE courseCode="TM129" and itemTitle LIKE "%{}%" '.format('Robotics Study Week {}'.format(week)),DB.conn)
    # pages = pd.read_sql('SELECT * FROM htmlxml WHERE courseCode="TM351" and doctype!="HTML" '.format('Session {}'.format(session)),DB.conn)
    # if len(pages):
    # for each page, transform it
    check_outdir(output_path_stub)
    transform_xml2md(row["xml"], output_path_stub=output_path_stub)

    imgdict = {}
    # for each page get the image links
    for page in os.listdir(output_path_dir):
        imgkeys = get_imgkeys_from_md(md_filepath="{}/{}".format(output_path_dir, page))

        # for each page, rewrite the links
        tmp_img, _imgdict = generate_imgdict(imgkeys, DB)
        imgdict = {**imgdict, **_imgdict}

        # for each page, save the images
        tmp_img.apply(
            lambda x: save_image_from_db(x, imgdir=os.path.join(_basedir, _imgdir)),
            axis=1,
        )

    crossmatch_xml_html_links(
        imgdict,
        imgdirpath=os.path.join("..", _imgdir),
        contentdir=output_path_dir,
        content_prefix="",
    )


# Py3.7 supports ordered_dict natively?
import collections


def section_item(title, url, not_numbered="true"):
    """ Create an ordered dict to add an item to the toc.yml """
    _contents = collections.OrderedDict()
    _contents["title"] = title
    _contents["url"] = url
    _contents["not_numbered"] = not_numbered
    return _contents


def section(title, url, sections=None, not_numbered="true", expand_sections="true"):
    """ Create an ordered dict to add an item to the toc.yml """
    _contents = section_item(title, url, not_numbered)
    if sections:
        _contents["sections"] = sections
    return _contents
