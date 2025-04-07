# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class XDoc(NamedElement):
    number: str | None = None
    state: str | None = None
    date: str | None = None
    publisher: str | None = None
    url: str | None = None
    position: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "XDoc":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))
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

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
