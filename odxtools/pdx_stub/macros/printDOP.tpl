{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printDiagCodedType(dct) -%}
<DIAG-CODED-TYPE BASE-DATA-TYPE="{{dct.base_data_type.value}}"
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if dct.base_type_encoding %}
                 BASE-TYPE-ENCODING="{{dct.base_type_encoding}}"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if dct.termination %}
                 TERMINATION="{{dct.termination}}"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
  {%- if dct.is_highlow_byte_order %}
                 IS-HIGHLOW-BYTE-ORDER="true"
  {%- else %}
                 IS-HIGHLOW-BYTE-ORDER="false"
  {%- endif %}
 {%- endfilter %}
 {%- filter odxtools_collapse_xml_attribute %}
                 xsi:type="{{dct.dct_type}}" >
 {%- endfilter %}
 {%- if dct.dct_type in ("STANDARD-LENGTH-TYPE", "LEADING-LENGTH-INFO-TYPE") %}
 <BIT-LENGTH>{{dct.bit_length}}</BIT-LENGTH>
 {%- else %}
 {%- if dct.max_length is not none %}
 <MAX-LENGTH>{{dct.max_length}}</MAX-LENGTH>
 {%- endif %}
 <MIN-LENGTH>{{dct.min_length}}</MIN-LENGTH>
 {%- endif %}
</DIAG-CODED-TYPE>
{%- endmacro -%}


{%- macro printPhysicalType(physical_type) %}
{%- if physical_type.display_radix is not none %}
<PHYSICAL-TYPE BASE-DATA-TYPE="{{physical_type.base_data_type.value}}" DISPLAY-RADIX="{{physical_type.display_radix.value}}" />
{%- elif physical_type.precision is not none   %}
<PHYSICAL-TYPE BASE-DATA-TYPE="{{physical_type.base_data_type.value}}">
 <PRECISION>{{physical_type.precision}}</PRECISION>
</PHYSICAL-TYPE>
{%- else %}
<PHYSICAL-TYPE BASE-DATA-TYPE="{{physical_type.base_data_type.value}}" />
{%- endif %}
{%- endmacro -%}


{%- macro printCompuMethod(cm) -%}
<COMPU-METHOD>
 <CATEGORY>{{cm.category}}</CATEGORY>
 {%- if cm.category == "TEXTTABLE" %}
 <COMPU-INTERNAL-TO-PHYS>
  <COMPU-SCALES>
  {%- for cs in cm.internal_to_phys %}
   <COMPU-SCALE>
   {%- if cs.short_label and cs.short_label.strip() %}
    <SHORT-LABEL>{{cs.short_label|e}}</SHORT-LABEL>
   {%- endif %}
   {%- if cs.description and cs.description.strip() %}
    <DESC>
    {{cs.description}}
    </DESC>
   {%- endif %}
   {%- if cs.lower_limit is not none %}
    <LOWER-LIMIT>{{cs.lower_limit.value}}</LOWER-LIMIT>
   {%- endif %}
   {%- if cs.upper_limit is not none %}
    <UPPER-LIMIT>{{cs.upper_limit.value}}</UPPER-LIMIT>
   {%- endif %}
   {%- if cs.compu_inverse_value is not none %}
    <COMPU-INVERSE-VALUE>
     <V>{{cs.compu_inverse_value | int }}</V>
    </COMPU-INVERSE-VALUE>
   {%- endif %}
    <COMPU-CONST>
     <VT>{{cs.compu_const | e }}</VT>
    </COMPU-CONST>
   </COMPU-SCALE>
  {%- endfor %}
  </COMPU-SCALES>
 </COMPU-INTERNAL-TO-PHYS>
 {%- elif cm.category == "LINEAR" %}
 <COMPU-INTERNAL-TO-PHYS>
		<COMPU-SCALES>
			<COMPU-SCALE>
   {%- if cm.internal_lower_limit.interval_type.value != "INFINITE" and cm.internal_lower_limit is not none %}
				<LOWER-LIMIT>{{cm.internal_lower_limit.value}}</LOWER-LIMIT>
   {%- endif %}
   {%- if cm.internal_upper_limit.interval_type.value != "INFINITE" and cm.internal_upper_limit is not none %}
				<UPPER-LIMIT>{{cm.internal_upper_limit.value}}</UPPER-LIMIT>
   {%- endif %}
				<COMPU-RATIONAL-COEFFS>
					<COMPU-NUMERATOR>
						<V>{{cm.offset | int}}</V>
						<V>{{(cm.factor*cm.denominator) | int}}</V>
					</COMPU-NUMERATOR>
   {%- if cm.denominator != 1 %}
					<COMPU-DENOMINATOR>
							<V>1</V>{# TODO: currently we always assume the offset to be an integer #}
							<V>{{cm.denominator | int}}</V>
					</COMPU-DENOMINATOR>
   {%- endif %}
				</COMPU-RATIONAL-COEFFS>
			</COMPU-SCALE>
		</COMPU-SCALES>
	</COMPU-INTERNAL-TO-PHYS>
 {%- elif cm.category == "SCALE-LINEAR" %}
 <COMPU-INTERNAL-TO-PHYS>
		<COMPU-SCALES>
  {%- for lm in cm.linear_methods %}
 		<COMPU-SCALE>
   {%- if lm.internal_lower_limit.interval_type.value != "INFINITE" and lm.internal_lower_limit is not none %}
				<LOWER-LIMIT>{{lm.internal_lower_limit.value}}</LOWER-LIMIT>
   {%- endif %}
   {%- if lm.internal_upper_limit.interval_type.value != "INFINITE" and lm.internal_upper_limit is not none %}
				<UPPER-LIMIT>{{lm.internal_upper_limit.value}}</UPPER-LIMIT>
   {%- endif %}
				<COMPU-RATIONAL-COEFFS>
					<COMPU-NUMERATOR>
							<V>{{(lm.offset) | int}}</V>
							<V>{{(lm.factor*lm.denominator) | int}}</V>
					</COMPU-NUMERATOR>
   {%- if lm.denominator != 1 %}
					<COMPU-DENOMINATOR>
							<V>1</V>{# TODO: currently we always assume the offset to be an integer #}
							<V>{{lm.denominator | int}}</V>
					</COMPU-DENOMINATOR>
   {%- endif %}
				</COMPU-RATIONAL-COEFFS>
			</COMPU-SCALE>
  {%- endfor %}
		</COMPU-SCALES>
 </COMPU-INTERNAL-TO-PHYS>
 {%- elif cm.category == "TAB-INTP" %}
 <COMPU-INTERNAL-TO-PHYS>
  <COMPU-SCALES>
  {%- for idx in range( cm.internal_points | length ) %}
   <COMPU-SCALE>
    <LOWER-LIMIT INTERVAL-TYPE="CLOSED">{{ cm.internal_points[idx] }}</LOWER-LIMIT>
    <COMPU-CONST>
     <V>{{ cm.physical_points[idx] }}</V>
    </COMPU-CONST>
   </COMPU-SCALE>
  {%- endfor %}
  </COMPU-SCALES>
 </COMPU-INTERNAL-TO-PHYS>
 {%- endif %}
</COMPU-METHOD>
{%- endmacro -%}


{%- macro printDOP(dop, tag_name) %}
<{{tag_name}} ID="{{dop.odx_id.local_id}}">
 <SHORT-NAME>{{dop.short_name}}</SHORT-NAME>
 <LONG-NAME>{{dop.long_name|e}}</LONG-NAME>
{%- if dop.compu_method is defined %}
 {{ printCompuMethod(dop.compu_method)|indent(1) }}
{%- endif %}
{%- if dop.diag_coded_type is defined %}
 {{ printDiagCodedType(dop.diag_coded_type)|indent(1) -}}
{%- endif -%}
 {{ printPhysicalType(dop.physical_type)|indent(1) }}
{%- if dop.unit_ref %}
 <UNIT-REF ID-REF="{{ dop.unit_ref.ref_id }}" />
{%- endif %}
</{{tag_name}}>
{%- endmacro -%}


{%- macro printDTCDOP(dop) %}
<DTC-DOP ID="{{dop.odx_id.local_id}}">
 <SHORT-NAME>{{dop.short_name}}</SHORT-NAME>
 <LONG-NAME>{{dop.long_name}}</LONG-NAME>
 {{ printDiagCodedType(dop.diag_coded_type)|indent(1) -}}
 {{ printPhysicalType(dop.physical_type)|indent(1) }}
 {{ printCompuMethod(dop.compu_method)|indent(1) }}
 <DTCS>
 {%- for dtc in dop.dtcs %}
 {%- if dtc.dtc_ref is defined   %}
  <DTC-REF ID-REF="{{dop.dtc_ref.ref_id}}" />
 {%- else %}
  <DTC ID="{{dtc.odx_id.local_id}}">
   <SHORT-NAME>{{dtc.short_name}}</SHORT-NAME>
   <TROUBLE-CODE>{{dtc.trouble_code}}</TROUBLE-CODE>
  {%- if dtc.display_trouble_code is not none   %}
   <DISPLAY-TROUBLE-CODE>{{dtc.display_trouble_code}}</DISPLAY-TROUBLE-CODE>
  {%- endif %}
   <TEXT>{{dtc.text|e}}</TEXT>
  {%- if not dtc.level is none   %}
   <LEVEL>{{dtc.level}}</LEVEL>
  {%- endif %}
  </DTC>
 {%- endif %}
 {%- endfor %}
 </DTCS>
</DTC-DOP>
{%- endmacro -%}
