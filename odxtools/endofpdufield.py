# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional
from xml.etree import ElementTree

from odxtools.odxlink import OdxDocFragment

from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import odxassert
from .field import Field
from .odxtypes import ParameterValueDict, odxstr_to_bool
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
        physical_value: ParameterValueDict,
        encode_state: EncodeState,
        bit_position: int = 0,
    ) -> bytes:
        odxassert(
            bit_position == 0, "End of PDU field must be byte aligned. "
            "Is there an error in reading the .odx?")
        if isinstance(physical_value, dict):
            # If the value is given as a dict, the End of PDU field behaves like the underlying structure.
            return self.structure.convert_physical_to_bytes(physical_value, encode_state)
        else:
            odxassert(
                isinstance(physical_value, list),
                "The value of an End-of-PDU-field must be a list or a dict.")
            # If the value is given as a list, each list element is a encoded seperately using the structure.
            coded_rpc = bytes()
            for value in physical_value:
                coded_rpc += self.structure.convert_physical_to_bytes(value, encode_state)
            return coded_rpc

    def convert_bytes_to_physical(self, decode_state: DecodeState, bit_position: int = 0):
        decode_state = copy(decode_state)
        next_byte_position = decode_state.next_byte_position
        byte_code = decode_state.coded_message

        value = []
        while len(byte_code) > next_byte_position:
            # ATTENTION: the ODX specification is very misleading
            # here: it says that the item is repeated until the end of
            # the PDU, but it means that DOP of the items that are
            # repeated are identical, not their values
            new_value, next_byte_position = self.structure.convert_bytes_to_physical(
                decode_state, bit_position=bit_position)
            # Update next byte_position
            decode_state.next_byte_position = next_byte_position
            value.append(new_value)

        return value, next_byte_position
