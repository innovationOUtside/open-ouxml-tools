# open-ouxml-tools
Tools for working with (open) OU-XML docs

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/innovationOUtside/open-ouxml-tools/master)

Quick example:

Run in MyBinder, then from notebook homepage new menu, open a new terminal, then run:

```
# List units bby search keywords
ouxml_units --term "history scottish"

# Grab XML for an OpenLEarn unit
# For some reason, this may take ages:-(
ouxml_grab https://www.open.edu/openlearn/science-maths-technology/chemistry/the-molecular-world/content-section-1.1

# Generate markdown from OU-XML
ouxml2md --dbname openlearn_oer.db --outdir demo
```

Markdown files and images for the unit will appear in the `demo` directory.