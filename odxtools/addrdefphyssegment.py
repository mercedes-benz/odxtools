# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .physsegment import PhysSegment
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class AddrdefPhysSegment(PhysSegment):
    end_address: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "AddrdefPhysSegment":
        kwargs = dataclass_fields_asdict(PhysSegment.from_et(et_element, context))

        end_address = odxrequire(read_hex_binary(et_element.find("END-ADDRESS")))

        return AddrdefPhysSegment(end_address=end_address, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
