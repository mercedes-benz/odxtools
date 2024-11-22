# SPDX-License-Identifier: MIT
import textwrap
from io import StringIO
from typing import Iterable

from .compumethods.compucodecompumethod import CompuCodeCompuMethod
from .compumethods.identicalcompumethod import IdenticalCompuMethod
from .compumethods.limit import IntervalType
from .compumethods.linearcompumethod import LinearCompuMethod
from .compumethods.linearsegment import LinearSegment
from .compumethods.ratfunccompumethod import RatFuncCompuMethod
from .compumethods.ratfuncsegment import RatFuncSegment
from .compumethods.scalelinearcompumethod import ScaleLinearCompuMethod
from .compumethods.scaleratfunccompumethod import ScaleRatFuncCompuMethod
from .compumethods.texttablecompumethod import TexttableCompuMethod
from .dataobjectproperty import DataObjectProperty
from .dtcdop import DtcDop
from .dynamiclengthfield import DynamicLengthField
from .endofpdufield import EndOfPduField
from .exceptions import odxrequire
from .multiplexer import Multiplexer
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.matchingrequestparameter import MatchingRequestParameter
from .parameters.nrcconstparameter import NrcConstParameter
from .parameters.parameter import Parameter
from .parameters.parameterwithdop import ParameterWithDOP
from .parameters.reservedparameter import ReservedParameter
from .parameters.systemparameter import SystemParameter
from .parameters.tablekeyparameter import TableKeyParameter
from .parameters.tablestructparameter import TableStructParameter
from .paramlengthinfotype import ParamLengthInfoType
from .staticfield import StaticField


def _get_linear_segment_info(segment: LinearSegment) -> str:
    ll = segment.physical_lower_limit
    if ll is None or ll.interval_type == IntervalType.INFINITE:
        ll_str = "(-inf"
    else:
        ll_delim = '(' if ll.interval_type == IntervalType.OPEN else '['
        ll_str = f"{ll_delim}{ll._value!r}"

    ul = segment.physical_upper_limit
    if ul is None or ul.interval_type == IntervalType.INFINITE:
        ul_str = "inf)"
    else:
        ul_delim = ')' if ul.interval_type == IntervalType.OPEN else ']'
        ul_str = f"{ul._value!r}{ul_delim}"

    return f"{ll_str}, {ul_str}"


def _get_rat_func_segment_info(segment: RatFuncSegment) -> str:
    ll = segment.lower_limit
    if ll is None or ll.interval_type == IntervalType.INFINITE:
        ll_str = "(-inf"
    else:
        ll_delim = '(' if ll.interval_type == IntervalType.OPEN else '['
        ll_str = f"{ll_delim}{ll._value!r}"

    ul = segment.upper_limit
    if ul is None or ul.interval_type == IntervalType.INFINITE:
        ul_str = "inf)"
    else:
        ul_delim = ')' if ul.interval_type == IntervalType.OPEN else ']'
        ul_str = f"{ul._value!r}{ul_delim}"

    return f"{ll_str}, {ul_str}"


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
        elif isinstance(param, SystemParameter):
            of.write(
                f"{q}{param.short_name}{q}: <system; kind = \"{param.sysparam}\">; required = {param.is_required}\n"
            )
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
        if dop is None:
            of.write("{q}{param.short_name}{q}: <no DOP>\n")
            continue
        elif isinstance(dop, EndOfPduField):
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
        elif isinstance(dop, DataObjectProperty):
            # a "simple" DOP
            if (cm := dop.compu_method) is None:
                of.write(f"{q}{param.short_name}{q}: <no compu method>\n")
                continue

            if isinstance(cm, TexttableCompuMethod):
                of.write(f"{q}{param.short_name}{q}: enum; choices:\n")
                for scale in odxrequire(cm.compu_internal_to_phys).compu_scales:
                    val_str = ""
                    if scale.lower_limit is not None:
                        val_str = f"({repr(scale.lower_limit.value)})"

                    if scale.compu_const is None:
                        of.write(f"  <ERROR in ODX data: no value specified>\n")
                    else:
                        vt = scale.compu_const.vt
                        v = scale.compu_const.v
                        if vt is not None:
                            of.write(f"  \"{vt}\" {val_str}\n")
                        else:
                            of.write(f"  {v}\n")

            elif isinstance(cm, IdenticalCompuMethod):
                of.write(f"{q}{param.short_name}{q}: {dop.physical_type.base_data_type}\n")

            elif isinstance(cm, ScaleLinearCompuMethod):
                of.write(f"{q}{param.short_name}{q}: {dop.physical_type.base_data_type}")
                seg_list = [_get_linear_segment_info(x) for x in cm.segments]
                of.write(f"; ranges = {{ {', '.join(seg_list)} }}")

                unit = dop.unit
                unit_str = unit.display_name if unit is not None else None
                if unit_str is not None:
                    of.write(f"; unit: {unit_str}")

                of.write("\n")

            elif isinstance(cm, LinearCompuMethod):
                of.write(f"{q}{param.short_name}{q}: {dop.physical_type.base_data_type}")
                of.write(f"; range: {_get_linear_segment_info(cm.segment)}")

                unit = dop.unit
                unit_str = unit.display_name if unit is not None else None
                if unit_str is not None:
                    of.write(f"; unit: {unit_str}")

                of.write("\n")

            elif isinstance(cm, ScaleRatFuncCompuMethod):
                of.write(f"{q}{param.short_name}{q}: {dop.physical_type.base_data_type}")
                if cm._phys_to_int_segments is None:
                    of.write("<NOT ENCODABLE>")
                else:
                    seg_list = [_get_rat_func_segment_info(x) for x in cm._phys_to_int_segments]
                    of.write(f"; ranges = {{ {', '.join(seg_list)} }}")

                    unit = dop.unit
                    unit_str = unit.display_name if unit is not None else None
                    if unit_str is not None:
                        of.write(f"; unit: {unit_str}")

                    of.write("\n")

            elif isinstance(cm, RatFuncCompuMethod):
                of.write(f"{q}{param.short_name}{q}: {dop.physical_type.base_data_type}")
                if cm._phys_to_int_segment is None:
                    of.write("<NOT ENCODABLE>")
                else:
                    of.write(f"; range: {_get_rat_func_segment_info(cm._phys_to_int_segment)}")

                    unit = dop.unit
                    unit_str = unit.display_name if unit is not None else None
                    if unit_str is not None:
                        of.write(f"; unit: {unit_str}")

                of.write("\n")

            elif isinstance(cm, CompuCodeCompuMethod):
                of.write(f"{q}{param.short_name}{q}: {dop.physical_type.base_data_type}")
                of.write(f"; <programmatic translation>")

                of.write("\n")

            else:
                of.write(
                    f"{q}{param.short_name}{q}: unknown compu method {type(dop.compu_method).__name__}\n"
                )
        else:
            of.write(f"{q}{param.short_name}{q}: <unhandled DOP '{type(dop).__name__}'>\n")

    return of.getvalue()
