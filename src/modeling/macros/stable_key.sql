{% macro stable_key(expression) -%}
(('x' || substr(md5({{ expression }}), 1, 15))::bit(60)::bigint)
{%- endmacro %}
