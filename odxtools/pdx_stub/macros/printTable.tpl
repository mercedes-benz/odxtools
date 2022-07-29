{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printTable(table) %}
<TABLE ID="{{table.id}}">
 <SHORT-NAME>{{table.short_name}}</SHORT-NAME>
 <LONG-NAME>{{table.long_name|e}}</LONG-NAME>
{%- if table.key_dop_ref %}
 <KEY-DOP-REF ID-REF="{{ table.key_dop_ref }}" />
{%- endif %}
{%- for table_row in table.table_rows %}
 <TABLE-ROW ID="{{table_row.id}}">
  <SHORT-NAME>{{table_row.short_name}}</SHORT-NAME>
  <LONG-NAME>{{table_row.long_name|e}}</LONG-NAME>
  <KEY>{{table_row.key}}</KEY>
  {%- if table_row.structure_ref %}
  <STRUCTURE-REF ID-REF="{{ table_row.structure_ref }}" />
  {%- endif %}
 </TABLE-ROW>
{%- endfor %}
</TABLE>
{%- endmacro -%}
