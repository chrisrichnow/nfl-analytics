{# dbt prefixes custom schemas with the profile's default schema by default
   (e.g. "staging_marts"). Override so models land in exactly the schema
   named in dbt_project.yml (e.g. just "marts"). #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
