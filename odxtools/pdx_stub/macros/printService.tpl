{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2021 MBition GmbH
-#}

{%- import('macros/printAudience.tpl') as paud %}

{%- macro printService(service) -%}
{%- if service.semantic is not none %}
{%-  set semattrib = " SEMANTIC=\""+service.semantic+"\"" -%}
{%- else %}
{%-  set semattrib = " SEMANTIC=\"UNKNOWN\"" -%}
{%- endif -%}
<DIAG-SERVICE ID="{{service.id}}" {{semattrib}}>
 <SHORT-NAME>{{service.short_name}}</SHORT-NAME>
{%- if service.long_name and service.long_name.strip() %}
 <LONG-NAME>{{service.long_name|e}}</LONG-NAME>
{%- endif %}
{%- if service.description and service.description.strip() %}
 <DESC>
 {{service.description}}
 </DESC>
{%- endif %}
{%- if service.functional_class_refs %}
 <FUNCT-CLASS-REFS>
{%- for ref in service.functional_class_refs %}
  <FUNCT-CLASS-REF ID-REF="{{ref}}" />
{%- endfor %}
 </FUNCT-CLASS-REFS>
{%- endif%}
{%- if service.audience %}
 {{ paud.printAudience(service.audience)|indent(1) }}
{%- endif%}
 <REQUEST-REF ID-REF="{{service.request_ref_id}}"/>
{%- if service.pos_res_ref_ids %}
 <POS-RESPONSE-REFS>
{%- for ref in service.pos_res_ref_ids %}
  <POS-RESPONSE-REF ID-REF="{{ref}}" />
{%- endfor %}
 </POS-RESPONSE-REFS>
{%- endif%}
{%- if service.neg_res_ref_ids %}
 <NEG-RESPONSE-REFS>
{%- for ref in service.neg_res_ref_ids %}
  <NEG-RESPONSE-REF ID-REF="{{ref}}" />
{%- endfor %}
 </NEG-RESPONSE-REFS>
{%- endif%}
</DIAG-SERVICE>
{%- endmacro -%}
