{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printAdditionalAudience(audience) -%}
<ADDITIONAL-AUDIENCE ID="{{audience.odx_link_id.local_id}}">
 <SHORT-NAME>{{audience.short_name}}</SHORT-NAME>
{%- if audience.long_name %}
 <LONG-NAME>{{audience.long_name}}</LONG-NAME>
{%- endif %}
{%- if audience.description is string and audience.description.strip() %}
 <DESC>
{{audience.description}}
 </DESC>
{%- endif %}
</ADDITIONAL-AUDIENCE>
{%- endmacro -%}

{%- macro printAudience(audience) -%}
<AUDIENCE 
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if not audience.is_supplier %}
                 IS-SUPPLIER="false"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if not audience.is_development %}
                 IS-DEVELOPMENT="false"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if not audience.is_manufacturing %}
                 IS-MANUFACTURING="false"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if not audience.is_aftersales %}
                 IS-AFTERSALES="false"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if not audience.is_aftermarket %}
                 IS-AFTERMARKET="false"
  {%- endif %}
 {%- endfilter %} >
{%- if audience.enabled_audience_refs %}
 <ENABLED-AUDIENCE-REFS>
{%- for ref in audience.enabled_audience_refs %}
  <ENABLED-AUDIENCE-REF ID-REF="{{ref.ref_id}}" />
{%- endfor %}
 </ENABLED-AUDIENCE-REFS>
{%- endif%}
{%- if audience.disabled_audience_refs %}
 <DISABLED-AUDIENCE-REFS>
{%- for ref in audience.disabled_audience_refs %}
  <DISABLED-AUDIENCE-REF ID-REF="{{ref.ref_id}}" />
{%- endfor %}
 </DISABLED-AUDIENCE-REFS>
{%- endif%}
</AUDIENCE>
{%- endmacro -%}
