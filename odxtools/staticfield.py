# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise, odxrequire
from .field import Field
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class StaticField(Field):
    """Array of a fixed number of structure objects"""
    fixed_number_of_items: int
    item_byte_size: int

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "StaticField":
        kwargs = dataclass_fields_asdict(Field.from_et(et_element, doc_frags))

        fixed_number_of_items = int(odxrequire(et_element.findtext('FIXED-NUMBER-OF-ITEMS')))
        item_byte_size = int(odxrequire(et_element.findtext('ITEM-BYTE-SIZE')))

        return StaticField(
            fixed_number_of_items=fixed_number_of_items, item_byte_size=item_byte_size, **kwargs)

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        return odxlinks

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    @override
    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

    @override
    def convert_physical_to_bytes(
        self,
        physical_value: ParameterValue,
        encode_state: EncodeState,
        bit_position: int = 0,
    ) -> bytes:
        if not isinstance(physical_value,
                          (tuple, list)) or len(physical_value) != self.fixed_number_of_items:
            odxraise(f"Value for static field '{self.short_name}' "
                     f"must be a list of size {self.fixed_number_of_items}")

        result = bytearray()
        for val in physical_value:
            if not isinstance(val, dict):
                odxraise(f"The individual parameter values for static field '{self.short_name}' "
                         f"must be dictionaries for structure '{self.structure.short_name}'")

            data = self.structure.convert_physical_to_bytes(val, encode_state)

            if len(data) > self.item_byte_size:
                odxraise(f"Insufficient item byte size for static field {self.short_name}: "
                         f"Is {self.item_byte_size} bytes, but need at least {len(data)} bytes")
                data = data[:self.item_byte_size]
            elif len(data) < self.item_byte_size:
                # add some padding bytes
                data = data.ljust(self.item_byte_size, b'\x00')

            result += data

        return result

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        odxassert(decode_state.cursor_bit_position == 0,
                  "No bit position can be specified for static length fields!")

        result: List[ParameterValue] = []
        for _ in range(self.fixed_number_of_items):
            orig_cursor = decode_state.cursor_byte_position

            if decode_state.cursor_byte_position - orig_cursor > self.item_byte_size:
                odxraise(f"Insufficient item byte size for static field {self.short_name}: "
                         f"Is {self.item_byte_size} bytes, but need at least "
                         f"{decode_state.cursor_byte_position - orig_cursor} bytes")

            result.append(self.structure.decode_from_pdu(decode_state))

            decode_state.cursor_byte_position = orig_cursor + self.item_byte_size

        return result
