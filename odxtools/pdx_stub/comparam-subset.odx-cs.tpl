{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2021-2022 MBition GmbH
 #
 # This template writes an .odx-cs file for a communication
 # parameter subset.
-#}
{%- import('macros/printVariant.tpl') as pv -%}
{%- import('macros/printComparam.tpl') as pcp -%}
{%- import('macros/printAdminData.tpl') as pad -%}
{%- import('macros/printCompanyData.tpl') as pcd -%}
{%- import('macros/printDOP.tpl') as pdop %}
{%- import('macros/printUnitSpec.tpl') as pus %}
{#- -#}

<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<ODX MODEL-VERSION="2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
 <!-- Written using odxtools {{odxtools_version}} -->
 <COMPARAM-SUBSET ID="{{comparam_subset.odx_id.local_id}}"
                  CATEGORY="{{comparam_subset.category}}" >
   <SHORT-NAME>{{comparam_subset.short_name}}</SHORT-NAME>
   {%- if comparam_subset.long_name is not none %}
   <LONG-NAME>{{comparam_subset.long_name|e}}</LONG-NAME>
   {%- endif %}
   {%- if comparam_subset.description and comparam_subset.description.strip() %}
   <DESC>
     {{comparam_subset.description}}
   </DESC>
   {%- endif %}
   {%- if comparam_subset.admin_data is not none %}
   {{- pad.printAdminData(comparam_subset.admin_data) | indent(3) }}
   {%- endif %}
   {%- if comparam_subset.company_datas is not none %}
   <COMPANY-DATAS>
     {%- for cd in comparam_subset.company_datas %}
     {{- pcd.printCompanyData(cd) | indent(5, first=True) }}
     {%- endfor %}
   </COMPANY-DATAS>
   {%- endif %}
   {% set num_simple_cps = 0 %}
   {% set num_complex_cps = 0 %}
   {%- for cp in comparam_subset.comparams %}
   {#
    # This is slightly hacky: To distinguish complex and simple
    # communication parameters, we check if the 'cp' object has a
    # 'comparams' attribute. If it does, it is a complex parameter.
    #}
   {%- if not hasattr(cp, 'comparams') %}
   {%- set num_simple_cps = num_simple_cps + 1 %}
   {%- else %}
   {%- set num_complex_cps = num_complex_cps + 1 %}
   {%- endif %}
   {%- endfor %}

   {%- if num_simple_cps > 0 %}
   <COMPARAMS>
     {%- for cp in comparam_subset.comparams %}
     {#
      # This is slightly hacky: To distinguish complex and simple
      # communication parameters, we check if the 'cp' object has a
      # 'comparams' attribute. If it does, it is a complex parameter.
      #}
     {%- if not hasattr(cp, 'comparams') %}
     {{- pcp.printSimpleComparam(cp) | indent(5, first=True) }}
     {%- endif %}
     {%- endfor %}
   </COMPARAMS>
   {%- endif %}
   {%- if num_complex_cps > 0 %}
   <COMPLEX-COMPARAMS>
     {%- for cp in comparam_subset.comparams %}
     {#
      # This is slightly hacky: To distinguish complex and simple
      # communication parameters, we check if the 'cp' object has a
      # 'comparams' attribute. If it does, it is a complex parameter.
      #}
     {%- if hasattr(cp, 'comparams') %}
     {{- pcp.printComplexComparam(cp) | indent(5, first=True) }}
     {%- endif %}
     {%- endfor %}
   </COMPLEX-COMPARAMS>
   {%- endif %}
   {% if comparam_subset.data_object_props %}
   <DATA-OBJECT-PROPS>
     {%- for dop in comparam_subset.data_object_props %}
     {{- pdop.printDOP(dop, "DATA-OBJECT-PROP") | indent(2, first=True) }}
     {%- endfor %}
   </DATA-OBJECT-PROPS>
   {% endif %}
   {% if comparam_subset.unit_spec %}
   {{ pus.printUnitSpec(comparam_subset.unit_spec) }}
   {% endif %}
 </COMPARAM-SUBSET>
</ODX>
