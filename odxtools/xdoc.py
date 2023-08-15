# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .element import BaseElement
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class XDoc(BaseElement):
    number: Optional[str]
    state: Optional[str]
    date: Optional[str]
    publisher: Optional[str]
    url: Optional[str]
    position: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "XDoc":
        kwargs = BaseElement.get_kwargs(et_element, doc_frags)
        number = et_element.findtext("NUMBER")
        state = et_element.findtext("STATE")
        date = et_element.findtext("DATE")
        publisher = et_element.findtext("PUBLISHER")
        url = et_element.findtext("URL")
        position = et_element.findtext("POSITION")

        return XDoc(
            number=number,
            state=state,
            date=date,
            publisher=publisher,
            url=url,
            position=position,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
