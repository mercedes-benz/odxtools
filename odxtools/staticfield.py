# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise, odxrequire
from .field import Field
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


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
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

    @override
    def encode_into_pdu(self, physical_value: ParameterValue, encode_state: EncodeState) -> None:

        if not isinstance(physical_value,
                          Sequence) or len(physical_value) != self.fixed_number_of_items:
            odxraise(f"Value for static field '{self.short_name}' "
                     f"must be a list of size {self.fixed_number_of_items}")

        orig_is_end_of_pdu = encode_state.is_end_of_pdu
        encode_state.is_end_of_pdu = False
        for i, val in enumerate(physical_value):
            if not isinstance(val, dict):
                odxraise(f"The individual parameter values for static field '{self.short_name}' "
                         f"must be dictionaries for structure '{self.structure.short_name}'")

            if i == len(physical_value) - 1:
                encode_state.is_end_of_pdu = orig_is_end_of_pdu

            pos_before = encode_state.cursor_byte_position
            self.structure.encode_into_pdu(val, encode_state)
            pos_after = encode_state.cursor_byte_position

            if pos_after - pos_before > self.item_byte_size:
                odxraise(
                    f"Insufficient item byte size for static field {self.short_name}: "
                    f"Is {self.item_byte_size} bytes, but need at least {pos_after - pos_before} bytes"
                )
                encode_state.cursor_byte_position = pos_before + self.item_byte_size
            elif pos_after - pos_before < self.item_byte_size:
                # add some padding bytes
                encode_state.emplace_bytes(b'\x00' * (self.item_byte_size -
                                                      (pos_after - pos_before)))

        encode_state.is_end_of_pdu = orig_is_end_of_pdu

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        odxassert(decode_state.cursor_bit_position == 0,
                  "No bit position can be specified for static length fields!")

        orig_origin = decode_state.origin_byte_position
        decode_state.origin_byte_position = decode_state.cursor_byte_position

        result: List[ParameterValue] = []
        for _ in range(self.fixed_number_of_items):
            orig_cursor = decode_state.cursor_byte_position

            if decode_state.cursor_byte_position - orig_cursor > self.item_byte_size:
                odxraise(f"Insufficient item byte size for static field {self.short_name}: "
                         f"Is {self.item_byte_size} bytes, but need at least "
                         f"{decode_state.cursor_byte_position - orig_cursor} bytes")

            result.append(self.structure.decode_from_pdu(decode_state))

            decode_state.cursor_byte_position = orig_cursor + self.item_byte_size

        decode_state.origin_byte_position = orig_origin

        return result
