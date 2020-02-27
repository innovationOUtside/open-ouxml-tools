from setuptools import setup

setup(
    name="ouxml",
    packages=['ouxml'],
    version='0.0.1',
    include_package_data=True,
    package_data = {
        'ouxml' : ['xslt/*.xslt']},
    install_requires=[
        'Click',
        'requests',
        'xmltodict',
        'tqdm',
        'pandas',
        'lxml',
        'mechanicalsoup',
        'beautifulsoup4',
        'sqlite_utils',
        'markdownify',
        'jupytext',
        'markdown'
    ],
    entry_points='''
        [console_scripts]
        ouxml_grab = ouxml.cli:get_xml
        ouxml_units = ouxml.cli:get_units
        ouxml_db_units = ouxml.cli:get_db_units
        ouxml2md = ouxml.cli:ouxml2md_conversion
    ''',
)
