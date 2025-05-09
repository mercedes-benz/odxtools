# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import read_hex_binary


@dataclass(kw_only=True)
class Filter:
    filter_start: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Filter":
        filter_start = odxrequire(read_hex_binary(et_element.find("FILTER-START")))

        return Filter(filter_start=filter_start)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
