# open-ouxml-tools
Tools for working with (open) OU-XML docs

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/innovationOUtside/open-ouxml-tools/master)

Quick example:

Run in MyBinder, open this `README.md` from the notebook homepage and it will open in a notebook UI.

Run the code cells (or from the notebook cell menu, select `Run All`).

```bash
# List units bby search keywords
! ouxml_units --term "history scottish"
```

```bash
# Grab XML for an OpenLEarn unit
# For some reason, this may take ages:-(
! ouxml_grab https://www.open.edu/openlearn/science-maths-technology/chemistry/the-molecular-world/content-section-1.1
```

```bash
# Generate markdown from OU-XML
! ouxml2md --dbname openlearn_oer.db --outdir demo
```

Markdown files and images for the unit will appear in the `demo` directory.
