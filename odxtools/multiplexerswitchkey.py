# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .dataobjectproperty import DataObjectProperty
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class MultiplexerSwitchKey:
    """
    The object that determines the case to be used by a multiplexer
    """
    byte_position: int
    bit_position: int | None = None
    dop_ref: OdxLinkRef

    @property
    def dop(self) -> DataObjectProperty:
        return self._dop

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MultiplexerSwitchKey":
        byte_position = int(odxrequire(et_element.findtext("BYTE-POSITION")))
        bit_position_str = et_element.findtext("BIT-POSITION")
        bit_position = int(bit_position_str) if bit_position_str is not None else None
        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), context))

        return MultiplexerSwitchKey(
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_ref, DataObjectProperty)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
