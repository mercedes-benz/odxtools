# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from .decodestate import DecodeState
from .determinenumberofitems import DetermineNumberOfItems
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from .field import Field
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


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

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)
        self.determine_number_of_items._resolve_snrefs(diag_layer)

    def convert_physical_to_bytes(
        self,
        physical_value: ParameterValue,
        encode_state: EncodeState,
        bit_position: int = 0,
    ) -> bytes:

        odxassert(bit_position == 0, "No bit position can be specified for dynamic length fields!")
        if not isinstance(physical_value, list):
            odxraise(
                f"Expected a list of values for dynamic length field {self.short_name}, "
                f"got {type(physical_value)}", EncodeError)

        det_num_items = self.determine_number_of_items
        field_len = det_num_items.dop.convert_physical_to_bytes(
            len(physical_value), encode_state, det_num_items.bit_position or 0)

        # hack to emplace the length specifier at the correct location
        tmp = encode_state.coded_message
        encode_state.coded_message = bytearray()
        encode_state.emplace_atomic_value(field_len, self.short_name + ".num_items",
                                          det_num_items.byte_position)
        result = encode_state.coded_message
        encode_state.coded_message = tmp

        # if required, add padding between the length specifier and
        # the first item
        if len(result) < self.offset:
            result.extend([0] * (self.offset - len(result)))
        elif len(result) > self.offset:
            odxraise(f"The length specifier of field {self.short_name} overlaps "
                     f"with the first item!")

        for value in physical_value:
            result += self.structure.convert_physical_to_bytes(value, encode_state)

        return result

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        odxassert(decode_state.cursor_bit_position == 0,
                  "No bit position can be specified for dynamic length fields!")

        orig_origin = decode_state.origin_byte_position
        orig_cursor = decode_state.cursor_byte_position

        det_num_items = self.determine_number_of_items
        decode_state.origin_byte_position = decode_state.cursor_byte_position
        decode_state.cursor_byte_position = decode_state.origin_byte_position + det_num_items.byte_position
        decode_state.cursor_bit_position = det_num_items.bit_position or 0

        n = det_num_items.dop.decode_from_pdu(decode_state)

        if not isinstance(n, int):
            odxraise(f"Number of items specified by a dynamic length field {self.short_name} "
                     f"must be an integer (is: {type(n).__name__})")
        elif n < 0:
            odxraise(
                f"Number of items specified by a dynamic length field {self.short_name} "
                f"must be positive (is: {n})", DecodeError)
        else:
            decode_state.cursor_byte_position = decode_state.origin_byte_position + self.offset
            result: List[ParameterValue] = []
            for _ in range(n):
                result.append(self.structure.decode_from_pdu(decode_state))

        decode_state.origin_byte_position = orig_origin
        decode_state.cursor_byte_position = max(orig_cursor, decode_state.cursor_byte_position)

        return result
