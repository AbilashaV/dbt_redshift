{#-- redshift should use default instead of postgres --#}
{% macro redshift__dateadd(datepart, interval, from_date_or_timestamp) %}
    {{ return(default__dateadd(datepart, interval, from_date_or_timestamp)) }}
{% endmacro %}
