# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .physsegment import PhysSegment
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SizedefPhysSegment(PhysSegment):
    size: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SizedefPhysSegment":
        kwargs = dataclass_fields_asdict(PhysSegment.from_et(et_element, context))

        size = int(odxrequire(et_element.findtext("SIZE")) or "0")

        return SizedefPhysSegment(size=size, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
