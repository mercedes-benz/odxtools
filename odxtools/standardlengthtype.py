# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .odxtypes import DataType


@dataclass
class StandardLengthType(DiagCodedType):

    bit_length: int
    bit_mask: Optional[int]
    is_condensed_raw: Optional[bool]

    @property
    def dct_type(self) -> DctType:
        return "STANDARD-LENGTH-TYPE"

    def convert_internal_to_bytes(self, internal_value, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        return self._to_bytes(
            internal_value,
            bit_position,
            self.bit_length,
            self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
            bit_mask=self.bit_mask,
        )

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        return self._extract_internal(
            decode_state.coded_message,
            decode_state.next_byte_position,
            bit_position,
            self.bit_length,
            self.base_data_type,
            self.is_highlow_byte_order,
            bit_mask=self.bit_mask,
        )
