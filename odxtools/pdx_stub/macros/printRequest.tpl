{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- import('macros/printDOP.tpl') as pdop %}
{%- import('macros/printParam.tpl') as pp %}

{%- macro printRequest(request) -%}
<REQUEST ID="{{request.odx_link_id.local_id}}">
 <SHORT-NAME>{{request.short_name}}</SHORT-NAME>
{%- if request.long_name %}
 <LONG-NAME>{{request.long_name|e}}</LONG-NAME>
{%- endif %}
{%- if request.description and request.description.strip() %}
 <DESC>
 {{request.description}}
 </DESC>
{%- endif %}
{%- if request.parameters %}
 <PARAMS>
 {%- for param in request.parameters -%}
  {{pp.printParam(param)|indent(2)}}
 {%- endfor %}
 </PARAMS>
{%- endif %}
</REQUEST>
{%- endmacro -%}
