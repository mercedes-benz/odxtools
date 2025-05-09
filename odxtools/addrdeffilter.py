# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .filter import Filter
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class AddrdefFilter(Filter):
    filter_end: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "AddrdefFilter":
        kwargs = dataclass_fields_asdict(Filter.from_et(et_element, context))

        filter_end = odxrequire(read_hex_binary(et_element.find("FILTER-END")))

        return AddrdefFilter(filter_end=filter_end, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
