# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class PhysSegment(IdentifiableElement):
    fillbyte: int | None = None
    block_size: int | None = None
    start_address: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "PhysSegment":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        fillbyte = read_hex_binary(et_element.find("FILLBYTE"))
        block_size = 0
        if (bs_elem := et_element.find("BLOCK-SIZE")) is not None:
            block_size = int(odxrequire(bs_elem.text) or "0")
        start_address = odxrequire(read_hex_binary(et_element.find("START-ADDRESS")))

        return PhysSegment(
            fillbyte=fillbyte, block_size=block_size, start_address=start_address, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
