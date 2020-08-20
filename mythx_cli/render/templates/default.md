{% extends "layout.md" %}

{% block heading %}
# MythX Report for {{ target }}
{% endblock %}

{% block header %}
##  Report for {{ filename }}

{% endblock %}

{% block report %}
- **UUID:** [{{issue['uuid']}}](https://dashboard.mythx.io/#/console/analyses/{{ issue['uuid'] }})
- **Issue:** {{ issue['swcID'] }} - {{ issue['swcTitle'] }}
- **Severity:** {{ issue['severity']|title }}
- **Description:** {{ issue['description']['tail'] }}
- **Line:** {{ line['line'] }}
```
{{ line['content'] }}
```


{% endblock %}

{% block postamble %}
----------
Made with ♥ by [MythX CLI](https://github.com/dmuhs/mythx-cli)
{% endblock %}
