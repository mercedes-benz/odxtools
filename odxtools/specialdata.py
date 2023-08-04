# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class SpecialData:
    semantic_info: Optional[str]  # the "SI" attribute
    text_identifier: Optional[str]  # the "TI" attribute, specifies the language used
    value: str

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "SpecialData":
        semantic_info = et_element.get("SI")
        text_identifier = et_element.get("TI")
        value = et_element.text or ""

        return SpecialData(
            semantic_info=semantic_info, text_identifier=text_identifier, value=value)
