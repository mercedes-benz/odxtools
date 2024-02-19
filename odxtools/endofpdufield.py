# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

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

    def convert_physical_to_bytes(
        self,
        physical_values: ParameterValue,
        encode_state: EncodeState,
        bit_position: int = 0,
    ) -> bytes:

        odxassert(
            bit_position == 0, "End of PDU field must be byte aligned. "
            "Is there an error in reading the .odx?", EncodeError)
        if not isinstance(physical_values, list):
            odxraise(
                f"Expected a list of values for end-of-pdu field {self.short_name}, "
                f"got {type(physical_values)}", EncodeError)

        coded_message = b''
        for value in physical_values:
            coded_message += self.structure.convert_physical_to_bytes(value, encode_state)
        return coded_message

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        odxassert(not decode_state.cursor_bit_position,
                  "No bit position can be specified for end-of-pdu fields!")

        result: List[ParameterValue] = []
        while decode_state.cursor_byte_position < len(decode_state.coded_message):
            # ATTENTION: the ODX specification is very misleading
            # here: it says that the item is repeated until the end of
            # the PDU, but it means that DOP of the items that are
            # repeated are identical, not their values
            result.append(self.structure.decode_from_pdu(decode_state))

        return result
