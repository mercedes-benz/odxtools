{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printAdminData(admin_data) -%}
<ADMIN-DATA>
 {%- if admin_data.language is not none %}
 <LANGUAGE>{{admin_data.language}}</LANGUAGE>
 {%- endif %}
 {%- if admin_data.company_doc_infos is not none %}
 <COMPANY-DOC-INFOS>
  {%- for cdi in admin_data.company_doc_infos %}
  <COMPANY-DOC-INFO>
    <COMPANY-DATA-REF ID-REF="{{cdi.company_data_ref}}" />
   {%- if cdi.team_member_ref is not none %}
    <TEAM-MEMBER-REF ID-REF="{{cdi.team_member_ref}}" />
   {%- endif %}
   {%- if cdi.doc_label is not none %}
    <DOC-LABEL>{{cdi.doc_label}}</DOC-LABEL>
   {%- endif %}
  </COMPANY-DOC-INFO>
  {%- endfor %}
 </COMPANY-DOC-INFOS>
 {%- endif %}
 {%- if admin_data.doc_revisions is not none %}
 <DOC-REVISIONS>
  {%- for doc_revision in admin_data.doc_revisions %}
  <DOC-REVISION>
   {%- if doc_revision.team_member_ref is not none %}
   <TEAM-MEMBER-REF ID-REF="{{doc_revision.team_member_ref}}" />
   {%- endif %}
   {%- if doc_revision.revision_label is not none %}
   <REVISION-LABEL>{{doc_revision.revision_label}}</REVISION-LABEL>
   {%- endif %}
   {%- if doc_revision.state is not none %}
   <STATE>{{doc_revision.state}}</STATE>
   {%- endif %}
   <DATE>{{doc_revision.date}}</DATE>
   {%- if doc_revision.tool is not none %}
   <TOOL>{{doc_revision.tool}}</TOOL>
   {%- endif %}
   {%- if doc_revision.modifications|length > 0 %}
   <MODIFICATIONS>
    {%- for mod in doc_revision.modifications %}
    <MODIFICATION>
     {%- if mod.change is not none %}
     <CHANGE>{{mod.change}}</CHANGE>
     {%- endif %}
     {%- if mod.reason is not none %}
     <REASON>{{mod.reason}}</REASON>
     {%- endif %}
    </MODIFICATION>
    {%- endfor %}
   </MODIFICATIONS>
   {%- endif %}
  </DOC-REVISION>
  {%- endfor %}
 </DOC-REVISIONS>
 {%- endif %}
</ADMIN-DATA>
{%- endmacro -%}
