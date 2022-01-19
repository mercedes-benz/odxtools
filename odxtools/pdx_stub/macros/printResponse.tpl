{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- import('macros/printParam.tpl') as pp %}

{%- macro printResponse(resp, tag_name="POS-RESPONSE") -%}
<{{tag_name}} ID="{{resp.id}}">
 <SHORT-NAME>{{resp.short_name}}</SHORT-NAME>
 <LONG-NAME>{{resp.long_name|e}}</LONG-NAME>
{%- if resp.description and resp.description.strip() %}
 <DESC>
 {{resp.description}}
 </DESC>
{%- endif %}
{%- if resp.parameters %}
 <PARAMS>
{%- for param in resp.parameters -%}
  {{ pp.printParam(param)|indent(2) }}
{%- endfor %}
 </PARAMS>
{%- endif %}
</{{tag_name}}>
{%- endmacro -%}
