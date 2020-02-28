import click
import os
import pandas as pd
from sqlite_utils import Database

import ouxml.moodlescraper as mscpr
import ouxml.OU_XML2md_Converter as ouxml2md


def droptable(conn, table):
    cursor = conn.cursor()
    cursor.execute("""DROP TABLE IF EXISTS {}""".format(table))
    conn.commit()


@click.command()
@click.option(
    "--dbname",
    default="openlearn_oer.db",
    help="SQLite database name (default: openlearn_oer.db)",
)
@click.option('--newdb/--no-newdb', default=True)
@click.argument("url")
def get_xml(dbname, newdb, url):
    """Get OU-XML for an OpenLearn Unit from OpenLearn HTML URL."""
    # test='https://www.open.edu/openlearn/science-maths-technology/chemistry/the-molecular-world/content-section-1.1'
    mscpr.scrape_unit_openlearn_base(possible_sc_links=[url], dbname=dbname, newdb=newdb)


@click.command()
@click.option(
    "--term", default="", help="Get unit listing, optionally filtered by term."
)
def get_units(term):
    """Get unit listing, optionally filtered by term."""
    units = mscpr.getUnitLocations(term)
    for unit in units:
        print(unit["name"], unit["url"])


@click.command()
@click.option(
    "--dbname",
    default="openlearn_oer.db",
    help="SQLite database name (default: openlearn_oer.db)",
)
@click.option(
    "--term", default="", help="Get unit listing, optionally filtered by term."
)
def get_db_units(dbname, term):
    """List available units in database."""
    df = pd.read_sql(
        f'SELECT * FROM htmlxml WHERE LOWER(itemTitle) LIKE "%{term.lower()}%"', DB.conn
    )
    print()
    df.apply(lambda x: print(x["courseCode"], x["itemTitle"]), axis=1)


@click.command()
@click.option(
    "--dbname",
    default="openlearn_oer.db",
    help="SQLite database name (default: openlearn_oer.db)",
)
@click.option(
    "--outdir",
    default="oer_md",
    help="Markdown file output directory (default: oer_md)",
)
@click.option("--prefix", default="Part", help="Filename prefix (default: Part)")
def ouxml2md_conversion(dbname, outdir, prefix):
    """Convert item(s) in database to markdown."""

    def hackfornow(row, col="itemTitle", outdir="oer_md"):
        """Need to do this all properly, eg where lots of units in db..."""
        ouxml2md.transformer(DB.conn, col, row[col], outdir)

    outpath = os.path.join(outdir, prefix)
    print(f"Rendering files into dir: {outdir}")
    DB = Database(dbname)
    pages = pd.read_sql("SELECT * FROM htmlxml", DB.conn)
    pages.apply(hackfornow, outdir=outpath, axis=1)
    ouxml2md.openlearn_image_mapper(dbname, outdir, "images")
