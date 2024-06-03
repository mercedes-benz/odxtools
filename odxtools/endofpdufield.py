# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional, Sequence
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import EncodeError, odxassert, odxraise
from .field import Field
from .odxlink import OdxDocFragment
from .odxtypes import ParameterValue
from .utils import dataclass_fields_asdict


@dataclass
class EndOfPduField(Field):
    """End of PDU fields are structures that are repeated until the end of the PDU"""
    min_number_of_items: Optional[int]
    max_number_of_items: Optional[int]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EndOfPduField":
        kwargs = dataclass_fields_asdict(Field.from_et(et_element, doc_frags))

        if (min_n_str := et_element.findtext("MIN-NUMBER-OF-ITEMS")) is not None:
            min_number_of_items = int(min_n_str)
        else:
            min_number_of_items = None
        if (max_n_str := et_element.findtext("MAX-NUMBER-OF-ITEMS")) is not None:
            max_number_of_items = int(max_n_str)
        else:
            max_number_of_items = None

        eopf = EndOfPduField(
            min_number_of_items=min_number_of_items,
            max_number_of_items=max_number_of_items,
            **kwargs)

        return eopf

    @override
    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        odxassert(not encode_state.cursor_bit_position,
                  "No bit position can be specified for end-of-pdu fields!")
        odxassert(encode_state.is_end_of_pdu,
                  "End-of-pdu fields can only be located at the end of PDUs!")

        if not isinstance(physical_value, Sequence):
            odxraise(
                f"Invalid type {type(physical_value).__name__} of physical "
                f"value for end-of-pdu field, expected a list", EncodeError)
            return

        orig_is_end_of_pdu = encode_state.is_end_of_pdu
        encode_state.is_end_of_pdu = False

        for i, value in enumerate(physical_value):
            if i == len(physical_value) - 1:
                encode_state.is_end_of_pdu = orig_is_end_of_pdu

            self.structure.encode_into_pdu(value, encode_state)

        encode_state.is_end_of_pdu = orig_is_end_of_pdu

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        odxassert(not decode_state.cursor_bit_position,
                  "No bit position can be specified for end-of-pdu fields!")

        orig_origin = decode_state.origin_byte_position
        decode_state.origin_byte_position = decode_state.cursor_byte_position

        result: List[ParameterValue] = []
        while decode_state.cursor_byte_position < len(decode_state.coded_message):
            # ATTENTION: the ODX specification is very misleading
            # here: it says that the item is repeated until the end of
            # the PDU, but it means that DOP of the items that are
            # repeated are identical, not their values
            result.append(self.structure.decode_from_pdu(decode_state))

        decode_state.origin_byte_position = orig_origin

        return result
