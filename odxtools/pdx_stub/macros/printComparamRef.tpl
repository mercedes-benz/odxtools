{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2021 MBition GmbH
-#}

{%- macro printComparamRef(cp) -%}
 {%- if cp.id_ref.startswith("ISO_15765_2.") %}
 {%-  set doc_ref = "ISO_11898_2_DWCAN" %}
 {%- elif cp.id_ref.startswith("ISO_15765_2.") %}
 {%-  set doc_ref = "ISO_15765_2" %}
 {%- elif cp.id_ref.startswith("ISO_15765_3.") %}
 {%-  set doc_ref = "ISO_15765_3" %}
 {%- else %}
 {%-  set doc_ref = "TODOUNKNOWN" %}
 {%- endif %}
<COMPARAM-REF ID-REF="{{cp.id_ref}}" DOCREF="doc_ref" DOCTYPE="COMPARAM-SUBSET">
 {%- if cp.value is iterable and cp.value is not string %}
 <COMPLEX-VALUE>
  {%- for val in cp.value %}
   {%- if val is not none %}
  <SIMPLE-VALUE>{{val}}</SIMPLE-VALUE>
   {%- else %}
  <SIMPLE-VALUE />
   {%- endif %}
  {%- endfor %}
 </COMPLEX-VALUE>
 {%- else %}
 <SIMPLE-VALUE>{{cp.value}}</SIMPLE-VALUE>
  {%- if cp.description is string and cp.description.strip() %}
  <DESC>
{{cp.description}}
  </DESC>
  {%- endif %}
 {%- endif %}
 <PROTOCOL-SNREF SHORT-NAME="TODO"/>
</COMPARAM-REF>
{%- endmacro -%}
