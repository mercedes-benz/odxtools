# SPDX-License-Identifier: MIT
import textwrap
from io import StringIO
from typing import Iterable

from .compumethods.identicalcompumethod import IdenticalCompuMethod
from .compumethods.limit import IntervalType
from .compumethods.linearcompumethod import LinearCompuMethod
from .compumethods.texttablecompumethod import TexttableCompuMethod
from .dataobjectproperty import DataObjectProperty
from .dtcdop import DtcDop
from .dynamiclengthfield import DynamicLengthField
from .endofpdufield import EndOfPduField
from .exceptions import odxrequire
from .multiplexer import Multiplexer
from .odxtypes import DataType
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.matchingrequestparameter import MatchingRequestParameter
from .parameters.nrcconstparameter import NrcConstParameter
from .parameters.parameter import Parameter
from .parameters.parameterwithdop import ParameterWithDOP
from .parameters.reservedparameter import ReservedParameter
from .parameters.tablekeyparameter import TableKeyParameter
from .parameters.tablestructparameter import TableStructParameter
from .paramlengthinfotype import ParamLengthInfoType
from .staticfield import StaticField


def parameter_info(param_list: Iterable[Parameter], quoted_names: bool = False) -> str:
    q = "'" if quoted_names else ""
    of = StringIO()
    for param in param_list:
        if isinstance(param, CodedConstParameter):
            of.write(f"{q}{param.short_name}{q}: const = {param._coded_value_str}\n")
            continue
        elif isinstance(param, MatchingRequestParameter):
            of.write(f"{q}{param.short_name}{q}: <matches request>\n")
            continue
        elif isinstance(param, NrcConstParameter):
            of.write(f"{q}{param.short_name}{q}: const; choices = {param.coded_values}\n")
            continue
        elif isinstance(param, ReservedParameter):
            of.write(f"{q}{param.short_name}{q}: <reserved>\n")
            continue
        elif isinstance(param, TableKeyParameter):
            of.write(
                f"{q}{param.short_name}{q}: <optional> table key; table = '{param.table.short_name}'; choices:\n"
            )
            for tr in param.table.table_rows:
                of.write(f"  '{tr.short_name}',\n")

            continue
        elif isinstance(param, TableStructParameter):
            of.write(
                f"{q}{param.short_name}{q}: table struct; key = '{param.table_key.short_name}'; choices:\n"
            )
            for tr in param.table_key.table.table_rows:
                of.write(f"  ('{tr.short_name}',\n")
                of.write(f"   {{\n")
                of.write(
                    textwrap.indent(
                        parameter_info(odxrequire(tr.structure).parameters, True), "    "))
                of.write(f"   }}),\n")

            continue
        elif not isinstance(param, ParameterWithDOP):
            of.write(
                f"{q}{param.short_name}{q}: <unhandled parameter type '{type(param).__name__}'>\n")
            continue

        dop = param.dop
        if isinstance(dop, EndOfPduField):
            of.write(f"{q}{param.short_name}{q}: list({{\n")
            of.write(textwrap.indent(parameter_info(dop.structure.parameters, True), "  "))
            of.write(f"}})\n")
            continue
        elif isinstance(dop, StaticField):
            of.write(f"{q}{param.short_name}{q}: length={dop.fixed_number_of_items}; list({{\n")
            of.write(textwrap.indent(parameter_info(dop.structure.parameters, True), "  "))
            of.write(f"}})\n")
            continue
        elif isinstance(dop, DynamicLengthField):
            of.write(f"{q}{param.short_name}{q}: list({{\n")
            of.write(textwrap.indent(parameter_info(dop.structure.parameters, True), "  "))
            of.write(f"}})\n")
            continue
        elif isinstance(dop, ParamLengthInfoType):
            of.write(f"{q}{param.short_name}{q}: ")
            of.write("<optional> ")
            of.write(f"int; length_key='{dop.length_key.short_name}'\n")
            continue
        elif isinstance(dop, DtcDop):
            of.write(f"{q}{param.short_name}{q}: ")
            of.write(f"DTC; choices:\n")
            for dtc in dop.dtcs:
                if dtc.display_trouble_code is not None:
                    dtc_desc = dtc.text and f"; \"{dtc.text}\""
                    of.write(
                        f"  '{dtc.display_trouble_code}' (0x{dtc.trouble_code:06x}{dtc_desc})\n")
                else:
                    dtc_desc = dtc.text and f" (\"{dtc.text}\")"
                    of.write(f"  0x{dtc.trouble_code:06x}{dtc_desc}\n")
            continue
        elif isinstance(dop, Multiplexer):
            of.write(f"{q}{param.short_name}{q}: ")
            if dop.default_case is not None:
                of.write(f"<optional>")
            of.write(f"multiplexer; choices:\n")
            for mux_case in dop.cases:
                of.write(f"  ({repr(mux_case.short_name)}, {{\n")
                if (struc := mux_case.structure) is not None:
                    of.write(textwrap.indent(parameter_info(struc.parameters, True), "    "))
                of.write(f"   }})\n")
            continue

        of.write(f"{q}{param.short_name}{q}")

        if dop is None:
            of.write(": <no DOP>\n")
            continue
        elif not isinstance(dop, DataObjectProperty):
            of.write(f": <unhandled DOP '{type(dop).__name__}'>\n")
            continue

        if (cm := dop.compu_method) is None:
            of.write(": <no compu method>\n")
            continue

        if isinstance(cm, TexttableCompuMethod):
            of.write(f": enum; choices:\n")
            for scale in odxrequire(cm.compu_internal_to_phys).compu_scales:
                val_str = ""
                if scale.lower_limit is not None:
                    val_str = f"({repr(scale.lower_limit.value)})"
                of.write(f"  {repr(scale.compu_const)}{val_str}\n")

        elif isinstance(cm, IdenticalCompuMethod):
            bdt = dop.physical_type.base_data_type
            if bdt in (DataType.A_UTF8STRING, DataType.A_UNICODE2STRING, DataType.A_ASCIISTRING):
                of.write(f": str")
            elif bdt == DataType.A_BYTEFIELD:
                of.write(f": bytes")
            elif bdt.name.startswith("A_FLOAT"):
                of.write(f": float")
            elif bdt.name.startswith("A_UINT"):
                of.write(f": uint")
            elif bdt.name.startswith("A_INT"):
                of.write(f": int")
            else:
                of.write(f": <unknown type {{ bdt.name }}>")

            of.write("\n")

        elif isinstance(cm, LinearCompuMethod):
            bdt = dop.physical_type.base_data_type
            if bdt in (DataType.A_UTF8STRING, DataType.A_UNICODE2STRING, DataType.A_ASCIISTRING):
                of.write(f": str")
            elif bdt in (DataType.A_BYTEFIELD,):
                of.write(f": bytes")
            elif bdt.name.startswith("A_FLOAT"):
                of.write(f": float")
            elif bdt.name.startswith("A_UINT"):
                of.write(f": uint")
            elif bdt.name.startswith("A_INT"):
                of.write(f": int")
            else:
                of.write(f": <unknown type>")

            ll = cm.segment.physical_lower_limit
            ul = cm.segment.physical_upper_limit
            if ll is None or ll.interval_type == IntervalType.INFINITE:
                ll_str = "(-inf"
            else:
                ll_delim = '(' if ll.interval_type == IntervalType.OPEN else '['
                ll_str = f"{ll_delim}{ll._value!r}"

            if ul is None or ul.interval_type == IntervalType.INFINITE:
                ul_str = "inf)"
            else:
                ul_delim = ')' if ul.interval_type == IntervalType.OPEN else ']'
                ul_str = f"{ul._value!r}{ul_delim}"
            of.write(f"; range: {ll_str}, {ul_str}")

            unit = dop.unit
            unit_str = unit.display_name if unit is not None else None
            if unit_str is not None:
                of.write(f"; unit: {unit_str}")

            of.write("\n")

    return of.getvalue()
