{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2021 MBition GmbH
-#}

{%- macro printEndOfPdu(eopdu) -%}
<END-OF-PDU-FIELD ID="{{eopdu.id}}">
 <SHORT-NAME>{{eopdu.short_name}}</SHORT-NAME>
 <LONG-NAME>{{eopdu.long_name|e}}</LONG-NAME>
 <BASIC-STRUCTURE-REF ID-REF="{{eopdu.structure_ref}}" />
</END-OF-PDU-FIELD>
{%- endmacro -%}
