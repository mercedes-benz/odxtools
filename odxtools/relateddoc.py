# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .description import Description
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .xdoc import XDoc


@dataclass(kw_only=True)
class RelatedDoc:
    xdoc: XDoc | None = None
    description: Description | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "RelatedDoc":
        xdoc: XDoc | None = None
        if (xdoc_elem := et_element.find("XDOC")) is not None:
            xdoc = XDoc.from_et(xdoc_elem, context)
        description = Description.from_et(et_element.find("DESC"), context)

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
