# SPDX-License-Identifier: MIT
from typing import List
from xml.etree import ElementTree

from .diagcodedtype import DiagCodedType
from .exceptions import odxraise
from .globals import xsi
from .leadinglengthinfotype import LeadingLengthInfoType
from .minmaxlengthtype import MinMaxLengthType
from .odxlink import OdxDocFragment
from .paramlengthinfotype import ParamLengthInfoType
from .standardlengthtype import StandardLengthType


def create_any_diag_coded_type_from_et(et_element: ElementTree.Element,
                                       doc_frags: List[OdxDocFragment]) -> DiagCodedType:
    dct_type = et_element.get(f"{xsi}type")
    if dct_type == "LEADING-LENGTH-INFO-TYPE":
        return LeadingLengthInfoType.from_et(et_element, doc_frags)
    elif dct_type == "MIN-MAX-LENGTH-TYPE":
        return MinMaxLengthType.from_et(et_element, doc_frags)
    elif dct_type == "PARAM-LENGTH-INFO-TYPE":
        return ParamLengthInfoType.from_et(et_element, doc_frags)
    elif dct_type == "STANDARD-LENGTH-TYPE":
        return StandardLengthType.from_et(et_element, doc_frags)

    odxraise(f"Unknown DIAG-CODED-TYPE {dct_type}", NotImplementedError)
    return DiagCodedType.from_et(et_element, doc_frags)
