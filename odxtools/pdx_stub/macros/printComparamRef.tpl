{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printComparamRef(cp) -%}
<COMPARAM-REF ID-REF="{{cp.id_ref.ref_id}}"
              DOCREF="{{comparam_subset_name(cp)}}"
              DOCTYPE="COMPARAM-SUBSET">
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
