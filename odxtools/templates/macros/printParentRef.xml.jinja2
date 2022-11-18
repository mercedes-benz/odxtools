{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printParentRef(par) -%}
{#-


WARNING: duck typing: assume the parent to be a document reference if
its not_inherited_diag_comms and not_inherited_dops are
empty. TODO: provide the xsi:type in the parent ref

-#}
{%- if not par.not_inherited_diag_comms and not  not par.not_inherited_dops %}
<PARENT-REF ID-REF="{{par.parent_ref.ref_id}}"
            DOCREF="{{par.parent_diag_layer.short_name}}"
            DOCTYPE="CONTAINER"
            xsi:type="FUNCTIONAL-GROUP-REF"/>
{%- else %}
<PARENT-REF ID-REF="{{par.parent_ref.ref_id}}"
            DOCREF="{{par.parent_diag_layer.short_name}}"
            DOCTYPE="CONTAINER"
            xsi:type="BASE-VARIANT-REF">
{%- if par.not_inherited_diag_comms %}
 <NOT-INHERITED-DIAG-COMMS>
{%-  for nidc in par.not_inherited_diag_comms %}
  <NOT-INHERITED-DIAG-COMM>
   <DIAG-COMM-SNREF SHORT-NAME="{{nidc}}"/>
  </NOT-INHERITED-DIAG-COMM>
{%-  endfor %}
 </NOT-INHERITED-DIAG-COMMS>
{%- endif %}
{%- if par.not_inherited_dops %}
 <NOT-INHERITED-DOPS>
{%-  for nidop in par.not_inherited_dops %}
  <NOT-INHERITED-DOP>
   <DOP-BASE-SNREF SHORT-NAME="{{nidop}}"/>
  </NOT-INHERITED-DOP>
{%-  endfor %}
 </NOT-INHERITED-DOPS>
{%- endif %}
</PARENT-REF>
{%- endif %}
{%- endmacro -%}

