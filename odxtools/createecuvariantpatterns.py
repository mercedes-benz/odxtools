# SPDX-License-Identifier: MIT
from typing import List, Optional
from xml.etree import ElementTree

from .ecuvariantpattern import EcuVariantPattern
from .odxlink import OdxDocFragment


def create_ecu_variant_patterns_from_et(et_element: Optional[ElementTree.Element],
                                        doc_frags: List[OdxDocFragment]) -> List[EcuVariantPattern]:

    if et_element is None:
        return []

    return [
        EcuVariantPattern.from_et(evp_elem, doc_frags)
        for evp_elem in et_element.iterfind("ECU-VARIANT-PATTERN")
    ]
