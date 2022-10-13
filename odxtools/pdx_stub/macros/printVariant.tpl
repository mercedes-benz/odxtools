{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- import('macros/printDOP.tpl') as pdop %}
{%- import('macros/printTable.tpl') as pt %}
{%- import('macros/printFunctionalClass.tpl') as pfc %}
{%- import('macros/printStructure.tpl') as pst %}
{%- import('macros/printEndOfPdu.tpl') as peopdu %}
{%- import('macros/printMux.tpl') as pm %}
{%- import('macros/printEnvData.tpl') as ped %}
{%- import('macros/printEnvDataDesc.tpl') as pedd %}
{%- import('macros/printUnitSpec.tpl') as punit %}
{%- import('macros/printService.tpl') as ps %}
{%- import('macros/printSingleEcuJob.tpl') as psej %}
{%- import('macros/printRequest.tpl') as prq %}
{%- import('macros/printResponse.tpl') as presp %}
{%- import('macros/printComparamRef.tpl') as pcom %}
{%- import('macros/printParentRef.tpl') as pparref %}
{%- import('macros/printAudience.tpl') as paud %}

{%- macro printVariant(dl, variant_tag) -%}
<{{variant_tag}} ID="{{dl.id.local_id}}">
 <SHORT-NAME>{{dl.short_name}}</SHORT-NAME>
{%- if dl.long_name %}
 <LONG-NAME>{{dl.long_name|e}}</LONG-NAME>
{%- endif %}
{%- if dl.description is string and dl.description.strip() %}
 <DESC>
{{dl.description}}
 </DESC>
{%- endif %}
{%- if dl.functional_classes %}
 <FUNCT-CLASSS>
{%- for fc in dl.functional_classes %}
   {{ pfc.printFunctionalClass(fc)|indent(3) }}
{%- endfor%}
 </FUNCT-CLASSS>
{%- endif %}
{%- if dl.local_diag_data_dictionary_spec.all_data_object_properties  %}
 <DIAG-DATA-DICTIONARY-SPEC>
{%- if dl.local_diag_data_dictionary_spec.dtc_dops  %}
  <DTC-DOPS>
 {%- for dop in dl.local_diag_data_dictionary_spec.dtc_dops -%}
  {{ pdop.printDTCDOP(dop)|indent(3) }}
 {%- endfor %}
  </DTC-DOPS>
{%- endif %}
{%- if dl.local_diag_data_dictionary_spec.env_data_descs  %}
  <ENV-DATA-DESCS>
 {%- for env_data_desc in dl.local_diag_data_dictionary_spec.env_data_descs -%}
  {{ pedd.printEnvDataDesc(env_data_desc)|indent(3) }}
 {%- endfor %}
  </ENV-DATA-DESCS>
{%- endif %}
 {%- if dl.local_diag_data_dictionary_spec.data_object_props %}
  <DATA-OBJECT-PROPS>
 {%- for dop in dl.local_diag_data_dictionary_spec.data_object_props %}
  {{- pdop.printDOP(dop, "DATA-OBJECT-PROP")|indent(3) }}
 {%- endfor %}
  </DATA-OBJECT-PROPS>
 {%- endif %}
 {%- if dl.local_diag_data_dictionary_spec.structures %}
  <STRUCTURES>
 {%- for st in dl.local_diag_data_dictionary_spec.structures %}
   {{ pst.printStructure(st)|indent(3) }}
 {%- endfor %}
  </STRUCTURES>
 {%- endif %}
 {%- if dl.local_diag_data_dictionary_spec.end_of_pdu_fields %}
  <END-OF-PDU-FIELDS>
 {%- for eopdu in dl.local_diag_data_dictionary_spec.end_of_pdu_fields %}
   {{ peopdu.printEndOfPdu(eopdu)|indent(3) }}
 {%- endfor %}
  </END-OF-PDU-FIELDS>
 {%- endif %}
  {%- if dl.local_diag_data_dictionary_spec.muxs %}
   <MUXS>
  {%- for mux in dl.local_diag_data_dictionary_spec.muxs %}
    {{ pm.printMux(mux)|indent(3) }}
  {%- endfor %}
   </MUXS>
  {%- endif %}
   {%- if dl.local_diag_data_dictionary_spec.env_datas %}
    <ENV-DATAS>
   {%- for env_data in dl.local_diag_data_dictionary_spec.env_datas %}
     {{ ped.printEnvData(env_data)|indent(3) }}
   {%- endfor %}
    </ENV-DATAS>
   {%- endif %}
 {%- if dl.local_diag_data_dictionary_spec.unit_spec %}
  {{ punit.printUnitSpec(dl.local_diag_data_dictionary_spec.unit_spec)|indent(2) }}
 {%- endif %}
 {%- if dl.local_diag_data_dictionary_spec.tables  %}
   <TABLES>
  {%- for table in dl.local_diag_data_dictionary_spec.tables -%}
   {{ pt.printTable(table)|indent(3) }}
  {%- endfor %}
   </TABLES>
 {%- endif %}
 </DIAG-DATA-DICTIONARY-SPEC>
{%- endif %}
{%- if dl._local_services or dl._local_single_ecu_jobs or dl._diag_comm_refs %}
 <DIAG-COMMS>
{%- for service in dl._local_services %}
  {{ ps.printService(service)|indent(2) }}
{%- endfor %}
{%- for job in dl._local_single_ecu_jobs %}
  {{ psej.printSingleEcuJob(job)|indent(2) }}
{%- endfor %}
{%- for dcr in dl._diag_comm_refs %}
  <DIAG-COMM-REF ID-REF="{{dcr.ref_id}}" />
{%- endfor %}
 </DIAG-COMMS>
{%- endif %}
{%- if dl.requests %}
 <REQUESTS>
{%- for req in dl.requests %}
  {{ prq.printRequest(req)|indent(2) }}
{%- endfor %}
 </REQUESTS>
{%- endif %}
{%- if dl.positive_responses %}
 <POS-RESPONSES>
{%- for resp in dl.positive_responses %}
  {{ presp.printResponse(resp)|indent(2) }}
{%- endfor %}
 </POS-RESPONSES>
{%- endif %}
{%- if dl.negative_responses %}
 <NEG-RESPONSES>
{%- for resp in dl.negative_responses %}
  {{ presp.printResponse(resp, "NEG-RESPONSE")|indent(2) }}
{%- endfor %}
 </NEG-RESPONSES>
{%- endif %}
{%- if dl.additional_audiences %}
 <ADDITIONAL-AUDIENCES>
{%- for audience in dl.additional_audiences %}
  {{ paud.printAdditionalAudience(audience)|indent(2) }}
{%- endfor %}
 </ADDITIONAL-AUDIENCES>
{%- endif %}
{%- if dl._local_communication_parameters %}
 <COMPARAM-REFS>
 {%- for cp in dl._local_communication_parameters -%}
 {{ pcom.printComparamRef(cp)|indent(2) }}
 {%- endfor %}
 </COMPARAM-REFS>
{%- endif %}
{%- if variant_tag == "PROTOCOL" %}
	<COMPARAM-SPEC-REF ID-REF="ISO_15765_3_on_ISO_15765_2" DOCREF="UDSOnCAN_CPS" DOCTYPE="COMPARAM-SPEC" />
{%- endif %}
{%- if dl.parent_refs %}
 <PARENT-REFS>
 {%- for parent in dl.parent_refs -%}
 {{ pparref.printParentRef(parent)|indent(2) }}
 {%- endfor %}
 </PARENT-REFS>
{%- endif %}
</{{variant_tag}}>
{%- endmacro -%}
