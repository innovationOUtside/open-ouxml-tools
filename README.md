# open-ouxml-tools
Tools for working with (open) OU-XML docs.

__THE TOOLS IN THIS REPO ARE LARGELY BROKEN AND/OR DEPRECATED. I'LL MIGRATE WORKING VERSIONS BACK IN TO THIS REPO AT SOME POINT, FOR NOW, THIS REPO IS BEST AVOIDED. FOR NOW, INSTEAD SEE [`innovationOUtside/ou-xml-validator`](https://github.com/innovationOUtside/ou-xml-validator) for OU-XML2MD/MD2OU0XML TOOLS,  [`innovationOUtside/sphinxcontrib-ou-xml-tags`](https://github.com/innovationOUtside/sphinxcontrib-ou-xml-tags) FOR MYST-OU-XML-TAG_EXTENSIONS, AND [`innovationoutside/openlearnCurriculumAssets`](https://innovationoutside.github.io/openlearnCurriculumAssets/intro.html) FOR EXAMPLES OF SCRAPING OU-XML CONTENT AND DECOMPOSING OU-XML SEMANTIC BLOCKS INTO A DB__

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/innovationOUtside/open-ouxml-tools/master)

Open demo direclty: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/innovationOUtside/open-ouxml-tools/HEAD?filepath=Demo.ipynb)

This package provides a range of command line and API tools for:

- grabbing OU-XML "source" versions of OpenLearn units, along with related image assets, and storing them in a SQLite3 database;
- converting OU-XML "source" documents to markdown files.

The markdown files can then be edited as simple text documents and used as part of markdown web publishing workflows.

The Binderised version of this repo allows you to test the package and generate markdown versions of OpenLearn units from their source OU-XML. The Binderised repo also installs Jupytext, which allows the markdown files to be edited in a Jupyter notebook interface. (Files cannot be saved directly back to Github from a MyBinder environment; they need to be exported and then uploaded to a Github repo, or example. The `nbarchive` extension is also installed in the Binderised environment to make it easier to export generated markdown files, etc.)

Quick example:

Run in MyBinder, open this `README.md` from the notebook homepage and it will open in a notebook UI.

Run the code cells (or from the notebook cell menu, select `Run All`).

```bash
# List units by search keywords
! ouxml_units --term "history scottish"
```

Having listed units of interest to you, you can grab scrape the OU-XML and image content from a selected URL with the following command (note that by default, a clean copy of the database is created each time you run the followig command; I still need to tweak the code to cleanly extract units from the db containing assets associated with multiple units):

```bash
# Grab XML for an OpenLearn unit
# For some reason, this may take ages:-(
! ouxml_grab https://www.open.edu/openlearn/science-maths-technology/chemistry/the-molecular-world/content-section-1.1
```
Once you have downloaded the assets, you can convert the XML to markdown files in a specified output directory (it will be automatically created if it does not already exist): 

```bash
# Generate markdown from OU-XML
! ouxml2md --dbname openlearn_oer.db --outdir demo
```

In the above example, markdown files and images for the unit will appear in the `demo` directory.

If you run this in MyBinder, from the notebook homepage, you can navigate to the folder the generated markdown was placed in. click on a markdown file link, and through the magic of Jupytext, edit it in a notebook UI.

We can also generate the markdown output from an XML file:

`ouxmlfile2md XML_FILE_PATH`


*OU staff may wonder whether the same approach can be used to convert OU-XML for current OU modules to markdown too. Yes it can... Get in touch...*
