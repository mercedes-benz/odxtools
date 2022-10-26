{#- -*- mode: sgml; tab-width: 1; indent-tabs-mode: nil -*-
 #
 # SPDX-License-Identifier: MIT
 # Copyright (c) 2022 MBition GmbH
-#}

{#- TODO: function classes

{%- macro printDTC_DOP(dop) -%}
<DTC-DOP ID="{{dop.odx_link_id.local_id}}">
 <SHORT-NAME>{{dop.short_name}}</SHORT-NAME>
 <LONG-NAME>{{dop.long_name|e}}</LONG-NAME>
</DTC-DOP>
{%- endmacro -%}

#}
