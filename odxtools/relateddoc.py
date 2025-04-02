# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .description import Description
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .xdoc import XDoc


@dataclass
class RelatedDoc:
    xdoc: XDoc | None
    description: Description | None

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: list[OdxDocFragment]) -> "RelatedDoc":
        xdoc: XDoc | None = None
        if (xdoc_elem := et_element.find("XDOC")) is not None:
            xdoc = XDoc.from_et(xdoc_elem, doc_frags)
        description = Description.from_et(et_element.find("DESC"), doc_frags)

        return RelatedDoc(
            xdoc=xdoc,
            description=description,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        if self.xdoc:
            result.update(self.xdoc._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.xdoc:
            self.xdoc._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.xdoc:
            self.xdoc._resolve_snrefs(context)
