# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from xml.etree import ElementTree

from typing_extensions import override

from .exceptions import odxassert
from .matchingbasevariantparameter import MatchingBaseVariantParameter
from .matchingparameter import MatchingParameter
from .odxdoccontext import OdxDocContext
from .variantpattern import VariantPattern


@dataclass(kw_only=True)
class EcuVariantPattern(VariantPattern):
    """ECU variant patterns are variant patterns used to identify the
    concrete variant of an ECU.
    """
    matching_parameters: list[MatchingParameter] = field(default_factory=list)

    @override
    def get_matching_parameters(self
                               ) -> list[MatchingParameter] | list[MatchingBaseVariantParameter]:
        return self.matching_parameters

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuVariantPattern":

        matching_parameters = [
            MatchingParameter.from_et(mp_el, context)
            for mp_el in et_element.iterfind("MATCHING-PARAMETERS/"
                                             "MATCHING-PARAMETER")
        ]

        odxassert(len(matching_parameters) > 0)  # required by ISO 22901-1 Figure 141
        return EcuVariantPattern(matching_parameters=matching_parameters)
