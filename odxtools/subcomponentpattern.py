# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext

if TYPE_CHECKING:
    from .matchingparameter import MatchingParameter


@dataclass(kw_only=True)
class SubComponentPattern:
    matching_parameters: list["MatchingParameter"] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SubComponentPattern":
        from .matchingparameter import MatchingParameter

        matching_parameters = [
            MatchingParameter.from_et(el, context)
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
