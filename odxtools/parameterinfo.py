# SPDX-License-Identifier: MIT
import re
from typing import Iterable, Union

from .compumethods.identicalcompumethod import IdenticalCompuMethod
from .compumethods.limit import IntervalType
from .compumethods.linearcompumethod import LinearCompuMethod
from .compumethods.texttablecompumethod import TexttableCompuMethod
from .dataobjectproperty import DataObjectProperty
from .endofpdufield import EndOfPduField
from .odxtypes import DataType
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.matchingrequestparameter import MatchingRequestParameter
from .parameters.parameter import Parameter
from .parameters.parameterwithdop import ParameterWithDOP
from .parameters.reservedparameter import ReservedParameter


def parameter_info(param_list: Iterable[Union[Parameter, EndOfPduField]]) -> str:
    result = ""
    for param in param_list:
        if isinstance(param, CodedConstParameter):
            result += f"{param.short_name} : const = {param._coded_value_str}\n"
            continue
        elif isinstance(param, MatchingRequestParameter):
            result += f"{param.short_name} : <matches request>\n"
            continue
        elif isinstance(param, ReservedParameter):
            result += f"{param.short_name} : <reserved>\n"
            continue
        elif not isinstance(param, ParameterWithDOP):
            result += f"{param.short_name} : <unhandled parameter type>\n"
            continue

        dop = param.dop

        if isinstance(dop, EndOfPduField):
            result += f"{param.short_name} : <optional> list({{\n"
            tmp = parameter_info(dop.structure.parameters).strip()
            tmp = re.sub("^", "  ", tmp)
            result += tmp + "\n"
            result += f"}})\n"
            continue

        result += f"{param.short_name}"

        if dop is None:
            result += ": <no DOP>\n"
            continue
        elif not isinstance(dop, DataObjectProperty):
            result += ": <unhandled DOP>\n"
            continue

        if (cm := dop.compu_method) is None:
            result += ": <no compu method>\n"
            continue

        if isinstance(cm, TexttableCompuMethod):
            result += f": enum; choices:\n"
            for scale in cm.internal_to_phys:
                result += f"  '{str(scale.compu_const)}'\n"

        elif isinstance(cm, IdenticalCompuMethod):
            bdt = dop.physical_type.base_data_type
            if bdt in (DataType.A_UTF8STRING, DataType.A_UNICODE2STRING, DataType.A_ASCIISTRING):
                result += f": str"
            elif bdt in (DataType.A_BYTEFIELD,):
                result += f": bytes"
            elif bdt.name.startswith("A_FLOAT"):
                result += f": float"
            elif bdt.name.startswith("A_UINT"):
                result += f": uint"
            elif bdt.name.startswith("A_INT"):
                result += f": int"
            else:
                result += f": <unknown type>"

            if (bl := dop.get_static_bit_length()) is not None:
                result += f"{bl}"

            result += "\n"

        elif isinstance(cm, LinearCompuMethod):
            result += f": float\n"
            ll = cm.physical_lower_limit
            ul = cm.physical_upper_limit
            result += (f" range: "
                       f"{'[' if ll.interval_type == IntervalType.CLOSED else '('}"
                       f"{ll.value!r}, "
                       f"{ul.value!r}"
                       f"{']' if ul.interval_type == IntervalType.CLOSED else ')'}\n")

            unit = dop.unit
            unit_str = unit.display_name if unit is not None else None
            if unit_str is not None:
                result += f" unit: {unit_str}\n"

    return result
