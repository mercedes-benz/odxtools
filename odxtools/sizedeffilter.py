# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .filter import Filter
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SizedefFilter(Filter):
    filter_size: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SizedefFilter":
        kwargs = dataclass_fields_asdict(Filter.from_et(et_element, context))

        filter_size = int(odxrequire(et_element.findtext("FILTER-SIZE")) or "0")

        return SizedefFilter(filter_size=filter_size, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
