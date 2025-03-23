# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Union
from xml.etree import ElementTree

from typing_extensions import override

from .exceptions import odxassert
from .matchingbasevariantparameter import MatchingBaseVariantParameter
from .matchingparameter import MatchingParameter
from .odxlink import OdxDocFragment
from .variantpattern import VariantPattern


@dataclass
class EcuVariantPattern(VariantPattern):
    """ECU variant patterns are variant patterns used to identify the
    concrete variant of an ECU.
    """
    matching_parameters: List[MatchingParameter]

    @override
    def get_matching_parameters(
            self) -> Union[List[MatchingParameter], List[MatchingBaseVariantParameter]]:
        return self.matching_parameters

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EcuVariantPattern":

        matching_parameters = [
            MatchingParameter.from_et(mp_el, doc_frags)
            for mp_el in et_element.iterfind("MATCHING-PARAMETERS/"
                                             "MATCHING-PARAMETER")
        ]

        odxassert(len(matching_parameters) > 0)  # required by ISO 22901-1 Figure 141
        return EcuVariantPattern(matching_parameters=matching_parameters)
