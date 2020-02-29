# jupyter nbconvert ouxml/OU_XML2md_Converter.ipynb --to script --template cleaner_py.tpl
#black ouxml/*.py 

{%- extends 'python.tpl' -%}

{% block in_prompt %}
{% endblock in_prompt %}

{% block markdowncell scoped %}
{%- if "docs" in cell.metadata.tags -%}
{{ super() }}
{%- else -%}
{%- endif -%}
{% endblock markdowncell %}

{% block input_group -%}
{%- if "active-ipynb" in cell.metadata.tags  -%}
{%- else -%}
{{ super() }}
{%- endif -%}
{% endblock input_group %}