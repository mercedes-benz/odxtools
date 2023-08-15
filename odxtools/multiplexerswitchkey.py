# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .dataobjectproperty import DataObjectProperty
from .exceptions import odxrequire
from .globals import logger
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class MultiplexerSwitchKey:
    """This class represents a Switch Key, which is used to select one of the cases defined in the Multiplexer."""

    byte_position: int
    bit_position: Optional[int]
    dop_ref: OdxLinkRef

    def __post_init__(self):
        self._dop: DataObjectProperty = None  # type: ignore

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MultiplexerSwitchKey":
        """Reads a Switch Key for a Multiplexer."""
        byte_position = int(odxrequire(et_element.findtext("BYTE-POSITION", "0")))
        bit_position_str = et_element.findtext("BIT-POSITION")
        bit_position = int(bit_position_str) if bit_position_str is not None else None
        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags))

        return MultiplexerSwitchKey(
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        dop = odxlinks.resolve(self.dop_ref)
        if isinstance(dop, DataObjectProperty):
            self._dop = dop
        else:
            logger.warning(
                f"DATA-OBJECT-PROP-REF '{self.dop_ref}' could not be resolved in SWITCH-KEY.")

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
