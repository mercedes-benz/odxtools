# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from .dataobjectproperty import DataObjectProperty
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class PositionedDataObjectProperty:
    """
    This class represents a wrapper for DataObjectProperty that adds position information
    used by Switch Key in the Multiplexer.
    used by Number Of Items in the DynamicLengthField.
    """

    byte_position: int
    bit_position: Optional[int]
    dop_ref: OdxLinkRef

    def __post_init__(self):
        self._dop: DataObjectProperty = None  # type: ignore

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "PositionedDataObjectProperty":
        byte_position = int(odxrequire(et_element.findtext("BYTE-POSITION", "0")))
        bit_position_str = et_element.findtext("BIT-POSITION")
        bit_position = int(bit_position_str) if bit_position_str is not None else None
        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags))

        return PositionedDataObjectProperty(
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
        )

    @property
    def dop(self) -> DataObjectProperty:
        return self._dop

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxrequire(odxlinks.resolve(self.dop_ref, DataObjectProperty))

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    def convert_physical_to_bytes(self, physical_value, encode_state: EncodeState) -> bytes:

        bit_position = self.bit_position if self.bit_position is not None else 0
        dop_bytes = self.dop.convert_physical_to_bytes(physical_value, encode_state, bit_position)

        return b'\0' * self.byte_position + dop_bytes

    def convert_bytes_to_physical(self, decode_state: DecodeState) -> Tuple[Any, int]:

        byte_code = decode_state.coded_message[decode_state.next_byte_position:]
        state = DecodeState(
            coded_message=byte_code[self.byte_position:],
            parameter_values={},
            next_byte_position=0,
        )
        bit_position_int = (self.bit_position if self.bit_position is not None else 0)
        return self.dop.convert_bytes_to_physical(state, bit_position=bit_position_int)
