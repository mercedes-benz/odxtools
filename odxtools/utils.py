# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Dict, Literal
from xml.etree import ElementTree

import re

def read_description_from_odx(et_element: ElementTree.Element):
    """Read a DESCRIPTION element. The element usually has the name DESC."""
    # TODO: Invent a better representation of a DESC element.
    #       This just represents it as XHTML string. 
    if et_element is None:
        return None
 
    raw_string = et_element.text or ''
    for e in et_element:
        raw_string += ElementTree.tostring(e, encoding='unicode')

    return raw_string.strip()


def read_element_id(et_element) -> Dict[Literal["short_name", "long_name", "description"], str]:
    """Read the elements "SHORT-NAME", "LONG-NAME" and "DESCRIPTION".

    Returns the dict
    ```python
    {
        "short_name": et_element.find("SHORT-NAME"),
        "long_name": et_element.find("LONG-NAME"),
        "description": read_description_from_odx(et_element.find("DESC"))
    }
    ```
    If `et_element` does not contain the elements "LONG-NAME" and "DESC",
    the returned dict does not contain the correspondig keys.

    A typical use for this function is reading an odx element
    that contains the group "ELEMENT-ID", e.g.,
    ```python
    def read_type_with_element_id_from_odx(et_element):
        element_id = read_element_id(et_element)
        return TypeWithElementID(**element_id)
    ```

    """
    d: Dict[Literal["short_name", "long_name", "description"], str] = {
        "short_name": et_element.findtext("SHORT-NAME")
    }
    if et_element.find("LONG-NAME") is not None:
        d["long_name"] = et_element.findtext("LONG-NAME")
    if et_element.find("DESC") is not None:
        d["description"] = read_description_from_odx(et_element.find("DESC"))
    return d

def parameter_info(param_list):
    from .endofpdufield import EndOfPduField
    from .parameters import CodedConstParameter
    from .parameters import MatchingRequestParameter
    from .parameters import ReservedParameter

    result = ""
    for param in param_list:
        if isinstance(param, CodedConstParameter):
            result += f"{param.short_name} : const = {param.coded_value}\n"
            continue
        elif isinstance(param, MatchingRequestParameter):
            result += f"{param.short_name} : <matches request>\n"
            continue
        elif isinstance(param, ReservedParameter):
            result += f"{param.short_name} : <reserved>\n"
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

        if (cm := dop.compu_method) is None:
            result += ": <no compu method>\n"
            continue

        if cm.category == "TEXTTABLE":
            result += f": enum; choices:\n"
            for scale in dop.compu_method.internal_to_phys:
                result += f"  '{scale.compu_const}'\n"

        elif cm.category == "IDENTICAL":
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

        elif cm.category == "LINEAR":
            result += f": float\n"
            ll = cm.physical_lower_limit
            ul = cm.physical_upper_limit
            result += \
                f" range: " \
                f"{'[' if ll.interval_type == IntervalType.CLOSED else '('}" \
                f"{ll.value}, " \
                f"{ul.value}" \
                f"{']' if ul.interval_type == IntervalType.CLOSED else ')'}\n"

    return result
