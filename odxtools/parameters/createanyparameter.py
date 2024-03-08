# SPDX-License-Identifier: MIT
from typing import List
from xml.etree import ElementTree

from ..exceptions import odxraise
from ..globals import xsi
from ..odxlink import OdxDocFragment
from .codedconstparameter import CodedConstParameter
from .dynamicparameter import DynamicParameter
from .lengthkeyparameter import LengthKeyParameter
from .matchingrequestparameter import MatchingRequestParameter
from .nrcconstparameter import NrcConstParameter
from .parameter import Parameter
from .physicalconstantparameter import PhysicalConstantParameter
from .reservedparameter import ReservedParameter
from .systemparameter import SystemParameter
from .tableentryparameter import TableEntryParameter
from .tablekeyparameter import TableKeyParameter
from .tablestructparameter import TableStructParameter
from .valueparameter import ValueParameter


def create_any_parameter_from_et(et_element: ElementTree.Element,
                                 doc_frags: List[OdxDocFragment]) \
                                 -> Parameter:
    parameter_type = et_element.get(f"{xsi}type")

    # Which attributes are set depends on the type of the parameter.
    if parameter_type == "VALUE":
        return ValueParameter.from_et(et_element, doc_frags)
    elif parameter_type == "CODED-CONST":
        return CodedConstParameter.from_et(et_element, doc_frags)
    elif parameter_type == "PHYS-CONST":
        return PhysicalConstantParameter.from_et(et_element, doc_frags)
    elif parameter_type == "SYSTEM":
        return SystemParameter.from_et(et_element, doc_frags)
    elif parameter_type == "LENGTH-KEY":
        return LengthKeyParameter.from_et(et_element, doc_frags)
    elif parameter_type == "NRC-CONST":
        return NrcConstParameter.from_et(et_element, doc_frags)
    elif parameter_type == "RESERVED":
        return ReservedParameter.from_et(et_element, doc_frags)
    elif parameter_type == "MATCHING-REQUEST-PARAM":
        return MatchingRequestParameter.from_et(et_element, doc_frags)
    elif parameter_type == "DYNAMIC":
        return DynamicParameter.from_et(et_element, doc_frags)
    elif parameter_type == "TABLE-STRUCT":
        return TableStructParameter.from_et(et_element, doc_frags)
    elif parameter_type == "TABLE-KEY":
        return TableKeyParameter.from_et(et_element, doc_frags)
    elif parameter_type == "TABLE-ENTRY":
        return TableEntryParameter.from_et(et_element, doc_frags)

    odxraise(f"I don't know about parameters of type {parameter_type}", NotImplementedError)
    return Parameter.from_et(et_element, doc_frags)
