{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- import('macros/printDOP.tpl') as pdop %}

{%- macro printParam(param) -%}
{%- if param.semantic is not none %}
{%-  set semattrib = " SEMANTIC=\""+param.semantic+"\"" -%}
{%- else %}
{%-  set semattrib = "" -%}
{%- endif -%}
{%- if param.parameter_type == "TABLE-KEY" and param.id is not none  %}
<PARAM {{semattrib}} ID="{{param.id}}" xsi:type="{{param.parameter_type}}">
{%- elif param.parameter_type == "SYSTEM" %}
<PARAM SYSPARAM="{{param.sysparam}}" xsi:type="{{param.parameter_type}}">
{%- else %}
<PARAM {{semattrib}} xsi:type="{{param.parameter_type}}">
{%- endif%}
 <SHORT-NAME>{{param.short_name}}</SHORT-NAME>
{%- if param.long_name %}
 <LONG-NAME>{{param.long_name|e}}</LONG-NAME>
{%- endif %}
{%- if param.byte_position is not none %}
 <BYTE-POSITION>{{param.byte_position}}</BYTE-POSITION>
{%- endif %}
{%- if param.parameter_type == "MATCHING-REQUEST-PARAM" and param.request_byte_position is defined %}
 <REQUEST-BYTE-POS>{{param.request_byte_position}}</REQUEST-BYTE-POS>
{%- elif param.bit_position != 0 %}
 <BIT-POSITION>{{param.bit_position}}</BIT-POSITION>
{%- endif %}
{%- if param.byte_length is defined and param.byte_length is not none %}
 <BYTE-LENGTH>{{param.byte_length}}</BYTE-LENGTH>
{%- endif %}
{%- if param.coded_value is defined %}
 <CODED-VALUE>{{param.coded_value}}</CODED-VALUE>
{%- elif param.physical_constant_value is defined %}
 <PHYS-CONSTANT-VALUE>{{param.physical_constant_value}}</PHYS-CONSTANT-VALUE>
{%- endif %}
{%- if param.dop_ref %}
 <DOP-REF ID-REF="{{param.dop_ref}}"/>
{%- elif param.dop is defined and param.dop is not none %}
 {{pdop.printDOP(param.dop)|indent(2)}}
{%- elif param.diag_coded_type is defined %}
 {{pdop.printDiagCodedType(param.diag_coded_type)|indent(2)}}
{%- elif param.parameter_type != "MATCHING-REQUEST-PARAM" %}
 {%- if param.bit_length is defined and param.bit_length is not none %}
  <BIT-LENGTH>{{param.bit_length}}</BIT-LENGTH>
 {%- endif %}
{%- endif %}
{%- if param.parameter_type == "TABLE-KEY" %}
 {%- if param.table_ref %}
 <TABLE-REF ID-REF="{{param.table_ref}}"/>
 {%- endif %}
 {%- if param.table_snref %}
 <TABLE-SNREF SHORT-NAME="{{param.table_snref}}"/>
 {%- endif %}
 {%- if param.table_row_snref %}
 <TABLE-ROW-SNREF SHORT-NAME="{{param.table_row_snref}}"/>
 {%- endif %}
 {%- if param.table_row_ref %}
 <TABLE-ROW-REF ID-REF="{{param.table_row_ref}}"/>
 {%- endif %}
{%- endif %}
{%- if param.parameter_type == "TABLE-STRUCT" %}
 {%- if param.table_key_ref %}
 <TABLE-KEY-REF ID-REF="{{param.table_key_ref}}"/>
 {%- endif %}
 {%- if param.table_key_snref %}
 <TABLE-KEY-SNREF SHORT-NAME="{{param.table_ref}}"/>
 {%- endif %}
{%- endif %}
</PARAM>
{%- endmacro -%}
