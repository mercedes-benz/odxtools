# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext

if TYPE_CHECKING:
    from .matchingparameter import MatchingParameter


@dataclass
class SubComponentPattern:
    matching_parameters: list["MatchingParameter"]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: list[OdxDocFragment]) -> "SubComponentPattern":
        from .matchingparameter import MatchingParameter

        matching_parameters = [
            MatchingParameter.from_et(el, doc_frags)
            for el in et_element.iterfind("MATCHING-PARAMETERS/MATCHING-PARAMETER")
        ]

        return SubComponentPattern(matching_parameters=matching_parameters)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}
        for mp in self.matching_parameters:
            result.update(mp._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for mp in self.matching_parameters:
            mp._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for mp in self.matching_parameters:
            mp._resolve_snrefs(context)
