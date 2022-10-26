{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{%- macro printEnvData(env_data) %}
<ENV-DATA ID="{{env_data.odx_link_id.local_id}}">
    <SHORT-NAME>{{env_data.short_name}}</SHORT-NAME>
    <LONG-NAME>{{env_data.long_name}}</LONG-NAME>
    <PARAMS>
        {%- for param in env_data.parameters %}
        <PARAM SEMANTIC="{{param.semantic}}" xsi:type="{{param.parameter_type}}">
          <SHORT-NAME>{{param.short_name}}</SHORT-NAME>
          <LONG-NAME>{{param.long_name}}</LONG-NAME>
          <BYTE-POSITION>{{param.byte_position}}</BYTE-POSITION>
          {%- if param.physical_constant_value %}
          <PHYS-CONSTANT-VALUE>{{param.physical_constant_value}}</PHYS-CONSTANT-VALUE>
          {%- endif %}
          <DOP-REF ID-REF="{{param.dop_ref.ref_id}}"/>
        </PARAM>
        {%- endfor %}
    </PARAMS>
    <ALL-VALUE/>
</ENV-DATA>
{%- endmacro -%}
