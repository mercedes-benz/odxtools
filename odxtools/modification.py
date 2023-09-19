# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Modification:
    change: Optional[str]
    reason: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Modification":
        change = et_element.findtext("CHANGE")
        reason = et_element.findtext("REASON")

        return Modification(change=change, reason=reason)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
