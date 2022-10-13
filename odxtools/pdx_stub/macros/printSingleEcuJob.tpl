{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- import('macros/printAudience.tpl') as paud %}

{%- macro printSingleEcuJob(job) -%}
<SINGLE-ECU-JOB ID="{{job.id.local_id}}"
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if job.oid %}
                OID="{{job.oid}}"
  {%- endif %}
 {%- endfilter -%}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if job.semantic %}
                SEMANTIC="{{job.semantic}}"
  {%- endif %}
 {%- endfilter -%}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if job.diagnostic_class %}
                DIAGNOSTIC-CLASS="{{job.diagnostic_class}}"
  {%- endif %}
 {%- endfilter -%}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if job.is_mandatory %}
                IS-MANDATORY="true"
  {%- endif %}
 {%- endfilter -%}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if not job.is_executable %}
                IS-EXECUTABLE="false"
  {%- endif %}
 {%- endfilter -%}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if job.is_final %}
                IS-FINAL="true"
  {%- endif %}
 {%- endfilter -%}
 >
 {{ printElementID(job)|indent(1) }}
{%- if job.functional_class_refs %}
 <FUNCT-CLASS-REFS>
{%- for ref in job.functional_class_refs %}
  <FUNCT-CLASS-REF ID-REF="{{ref.ref_id}}" />
{%- endfor %}
 </FUNCT-CLASS-REFS>
{%- endif %}
{%- if job.audience %}
 {{ paud.printAudience(job.audience)|indent(1) }}
{%- endif %}
 <PROG-CODES>
{%- for prog in job.prog_codes %}
  {{ printProgCode(prog)|indent(2) }}
{%- endfor %}
 </PROG-CODES>
{%- if job.input_params %}
 <INPUT-PARAMS>
{%- for param in job.input_params %}
  {{ printInputParam(param)|indent(2) }}
{%- endfor %}
 </INPUT-PARAMS>
{%- endif %}
{%- if job.output_params %}
 <OUTPUT-PARAMS>
{%- for param in job.output_params %}
  {{ printOutputParam(param)|indent(2) }}
{%- endfor %}
 </OUTPUT-PARAMS>
{%- endif %}
{%- if job.neg_output_params %}
 <NEG-OUTPUT-PARAMS>
{%- for param in job.neg_output_params %}
  {{ printNegOutputParam(param)|indent(2) }}
{%- endfor %}
 </NEG-OUTPUT-PARAMS>
{%- endif %}
</SINGLE-ECU-JOB>
{%- endmacro -%}


{%- macro printProgCode(prog) -%}
<PROG-CODE>
 <CODE-FILE>{{prog.code_file}}</CODE-FILE>
{%- if prog.encryption %}
 <ENCRYPTION>{{prog.encryption}}</ENCRYPTION>
{%- endif %}
 <SYNTAX>{{prog.syntax}}</SYNTAX>
 <REVISION>{{prog.revision}}</REVISION>
{%- if prog.entrypoint %}
 <ENTRYPOINT>{{prog.entrypoint}}</ENTRYPOINT>
{%- endif %}
{%- if prog.library_refs %}
 <LIBRARY-REFS>
 {%- for ref in prog.library_refs %}
   <LIBRARY-REF ID-REF="{{ref.ref_id}}" />
 {%- endfor %}
 </LIBRARY-REFS>
{%- endif %}
</PROG-CODE>
{%- endmacro -%}


{%- macro printInputParam(param) -%}
<INPUT-PARAM
{%- filter odxtools_collapse_xml_attribute %}
  {%- if param.semantic %}
                SEMANTIC="{{param.semantic}}"
  {%- endif %}
 {%- endfilter -%}
{%- filter odxtools_collapse_xml_attribute %}
  {%- if param.oid %}
                OID="{{param.oid}}"
  {%- endif %}
 {%- endfilter -%}
>
 {{ printElementID(param)|indent(1) }}
{%- if param.physical_default_value %}
 <PHYSICAL-DEFAULT-VALUE>{{param.physical_default_value}}</PHYSICAL-DEFAULT-VALUE>
{%- endif %}
 <DOP-BASE-REF ID-REF="{{param.dop_base_ref.ref_id}}" />
</INPUT-PARAM>
{%- endmacro -%}

{%- macro printOutputParam(param) -%}
<OUTPUT-PARAM ID="{{param.id.local_id}}"
{%- filter odxtools_collapse_xml_attribute %}
  {%- if param.oid %}
             OID="{{param.oid}}"
  {%- endif %}
 {%- endfilter -%}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if param.semantic %}
             SEMANTIC="{{param.semantic}}"
  {%- endif %}
 {%- endfilter -%}
>
 {{ printElementID(param)|indent(1) }}
 <DOP-BASE-REF ID-REF="{{param.dop_base_ref.ref_id}}" />
</OUTPUT-PARAM>
{%- endmacro -%}


{%- macro printNegOutputParam(param) -%}
<NEG-OUTPUT-PARAM>
 {{ printElementID(param)|indent(1) }}
 <DOP-BASE-REF ID-REF="{{param.dop_base_ref.ref_id}}" />
</NEG-OUTPUT-PARAM>
{%- endmacro -%}


{%- macro printElementID(element) -%}
 <SHORT-NAME>{{element.short_name}}</SHORT-NAME>
{%- if element.long_name and element.long_name.strip() %}
 <LONG-NAME>{{element.long_name|e}}</LONG-NAME>
{%- endif %}
{%- if element.description and element.description.strip() %}
 <DESC>
 {{element.description}}
 </DESC>
{%- endif %}
{%- endmacro -%}
