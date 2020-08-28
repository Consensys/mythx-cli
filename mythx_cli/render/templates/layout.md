{% block heading scoped %}{% endblock %}
{% block preamble scoped %}{% endblock %}
{% for filename, file_data in report_context.items() %}
{% block header scoped %}{% endblock %}
{% if file_data|rejectattr('issues')|join('')|length %}
{% for line in file_data %}
{% for issue in line['issues'] %}
{% block report scoped %}{% endblock %}
{% endfor %}
{% endfor %}
{% else %}
{% block no_issues_name scoped %}
*No issues have been found.*


{% endblock %}
{% endif %}
{% endfor %}
{% block postamble scoped %}{% endblock %}
