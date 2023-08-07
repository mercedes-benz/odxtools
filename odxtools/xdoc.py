# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxLinkDatabase, OdxLinkId
from .utils import create_description_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class XDoc:
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    number: Optional[str]
    state: Optional[str]
    date: Optional[str]
    publisher: Optional[str]
    url: Optional[str]
    position: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element) -> "XDoc":
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        number = et_element.findtext("NUMBER")
        state = et_element.findtext("STATE")
        date = et_element.findtext("DATE")
        publisher = et_element.findtext("PUBLISHER")
        url = et_element.findtext("URL")
        position = et_element.findtext("POSITION")

        return XDoc(
            short_name=short_name,
            long_name=long_name,
            description=description,
            number=number,
            state=state,
            date=date,
            publisher=publisher,
            url=url,
            position=position,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
