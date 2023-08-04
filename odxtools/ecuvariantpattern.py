# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .exceptions import odxassert, odxrequire
from .matchingparameter import MatchingParameter
from .odxlink import OdxDocFragment


@dataclass
class EcuVariantPattern:
    matching_parameters: List[MatchingParameter]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EcuVariantPattern":

        mp_collection_el = odxrequire(et_element.find("MATCHING-PARAMETERS"))

        matching_params = [
            MatchingParameter.from_et(mp_el, doc_frags)
            for mp_el in mp_collection_el.iterfind("MATCHING-PARAMETER")
        ]

        odxassert(len(matching_params) > 0)  # required by ISO 22901-1 Figure 141
        return EcuVariantPattern(matching_params)
