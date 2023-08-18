# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .utils import create_description_from_et
from .xdoc import XDoc

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class RelatedDoc:
    description: Optional[str]
    xdoc: Optional[XDoc]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "RelatedDoc":
        description = create_description_from_et(et_element.find("DESC"))

        xdoc: Optional[XDoc] = None
        if (xdoc_elem := et_element.find("XDOC")) is not None:
            xdoc = XDoc.from_et(xdoc_elem, doc_frags)

        return RelatedDoc(
            description=description,
            xdoc=xdoc,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        if self.xdoc:
            result.update(self.xdoc._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.xdoc:
            self.xdoc._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.xdoc:
            self.xdoc._resolve_snrefs(diag_layer)
