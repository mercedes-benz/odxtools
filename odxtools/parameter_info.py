# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Iterable, Union

from .dataobjectproperty import DataObjectProperty
from .endofpdufield import EndOfPduField
from .parameters import CodedConstParameter
from .parameters import MatchingRequestParameter
from .parameters import ReservedParameter
from .parameters import Parameter
from .parameters import ParameterWithDOP
from .endofpdufield import EndOfPduField
from .compumethods import Limit
from .compumethods import IntervalType
from .compumethods import IdenticalCompuMethod
from .compumethods import LinearCompuMethod
from .compumethods import TexttableCompuMethod

import re

def parameter_info(param_list : Iterable[Union[Parameter, EndOfPduField]]) -> str:
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
                result += f"  '{scale.compu_const}'\n"

        elif isinstance(cm, IdenticalCompuMethod):
            bdt = dop.physical_type.base_data_type.name
            if bdt in ("A_UTF8STRING", "A_UNICODE2STRING", "A_ASCIISTRING"):
                result += f": str"
            elif bdt in ("A_BYTEFIELD"):
                result += f": bytes"
            elif bdt.startswith("A_FLOAT"):
                result += f": float"
            elif bdt.startswith("A_UINT"):
                result += f": uint"
            elif bdt.startswith("A_INT"):
                result += f": int"
            else:
                result += f": <unknown type>"

            if dop.bit_length is not None:
                result += f"{dop.bit_length}\n"
            else:
                result += "\n"

        elif isinstance(cm, LinearCompuMethod):
            result += f": float\n"
            ll = cm.physical_lower_limit
            ul = cm.physical_upper_limit
            result += \
                f" range: " \
                f"{'[' if ll.interval_type == IntervalType.CLOSED else '('}" \
                f"{ll.value}, " \
                f"{ul.value}" \
                f"{']' if ul.interval_type == IntervalType.CLOSED else ')'}\n"

            unit = dop.unit
            unit_str = unit.display_name if unit is not None else None
            if unit_str is not None:
                result += f" unit: {unit_str}\n"

    return result
