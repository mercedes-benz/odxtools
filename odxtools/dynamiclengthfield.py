# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .determinenumberofitems import DetermineNumberOfItems
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from .field import Field
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class DynamicLengthField(Field):
    """Array of structure with length field"""
    offset: int
    determine_number_of_items: DetermineNumberOfItems

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DynamicLengthField":
        kwargs = dataclass_fields_asdict(Field.from_et(et_element, doc_frags))
        offset = int(odxrequire(et_element.findtext('OFFSET')))
        determine_number_of_items = DetermineNumberOfItems.from_et(
            odxrequire(et_element.find('DETERMINE-NUMBER-OF-ITEMS')),
            doc_frags,
        )
        return DynamicLengthField(
            offset=offset, determine_number_of_items=determine_number_of_items, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        odxlinks.update(self.determine_number_of_items._build_odxlinks())
        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)
        self.determine_number_of_items._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
        self.determine_number_of_items._resolve_snrefs(context)

    @override
    def encode_into_pdu(self, physical_value: ParameterValue, encode_state: EncodeState) -> None:

        odxassert(encode_state.cursor_bit_position == 0,
                  "No bit position can be specified for dynamic length fields!")

        if not isinstance(physical_value, Sequence):
            odxraise(
                f"Expected a list of values for dynamic length field {self.short_name}, "
                f"got {type(physical_value)}", EncodeError)

        # move the origin to the cursor position
        orig_origin = encode_state.origin_byte_position
        encode_state.origin_byte_position = encode_state.cursor_byte_position

        det_num_items = self.determine_number_of_items
        encode_state.cursor_bit_position = self.determine_number_of_items.bit_position or 0
        encode_state.cursor_byte_position = encode_state.origin_byte_position + det_num_items.byte_position
        det_num_items.dop.encode_into_pdu(len(physical_value), encode_state)

        if encode_state.cursor_byte_position - encode_state.origin_byte_position > self.offset:
            odxraise(f"The length specifier of field {self.short_name} overlaps "
                     f"with its first item!")

        encode_state.cursor_byte_position = encode_state.origin_byte_position + self.offset
        encode_state.cursor_bit_position = 0

        orig_is_end_of_pdu = encode_state.is_end_of_pdu
        encode_state.is_end_of_pdu = False
        for i, value in enumerate(physical_value):
            if i == len(physical_value) - 1:
                encode_state.is_end_of_pdu = orig_is_end_of_pdu

            self.structure.encode_into_pdu(value, encode_state)
        encode_state.is_end_of_pdu = orig_is_end_of_pdu

        # ensure the correct message size if the field is empty
        if len(physical_value) == 0:
            encode_state.emplace_bytes(b"")

        # move cursor and origin positions
        encode_state.origin_byte_position = orig_origin

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        odxassert(decode_state.cursor_bit_position == 0,
                  "No bit position can be specified for dynamic length fields!")

        orig_origin = decode_state.origin_byte_position

        det_num_items = self.determine_number_of_items
        decode_state.origin_byte_position = decode_state.cursor_byte_position
        decode_state.cursor_byte_position = decode_state.origin_byte_position + det_num_items.byte_position
        decode_state.cursor_bit_position = det_num_items.bit_position or 0

        n = det_num_items.dop.decode_from_pdu(decode_state)
        result: List[ParameterValue] = []

        if not isinstance(n, int):
            odxraise(f"Number of items specified by a dynamic length field {self.short_name} "
                     f"must be an integer (is: {type(n).__name__})")
        elif n < 0:
            odxraise(
                f"Number of items specified by a dynamic length field {self.short_name} "
                f"must be positive (is: {n})", DecodeError)
            n = 0

        decode_state.cursor_byte_position = decode_state.origin_byte_position + self.offset
        for _ in range(n):
            result.append(self.structure.decode_from_pdu(decode_state))

        decode_state.origin_byte_position = orig_origin

        return result
