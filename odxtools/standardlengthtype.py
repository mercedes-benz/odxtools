# SPDX-License-Identifier: MIT
from typing import Optional

from .decodestate import DecodeState
from .diagcodedtype import DiagCodedType
from .encodestate import EncodeState
from .odxtypes import DataType


class StandardLengthType(DiagCodedType):

    def __init__(
        self,
        *,
        base_data_type: DataType,
        bit_length: int,
        bit_mask: Optional[int],
        is_condensed_raw: Optional[bool],
        base_type_encoding: Optional[str],
        is_highlow_byte_order_raw: Optional[bool],
    ):
        super().__init__(
            base_data_type=base_data_type,
            dct_type="STANDARD-LENGTH-TYPE",
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw,
        )
        self.bit_length = bit_length
        self.bit_mask = bit_mask
        self.is_condensed_raw = is_condensed_raw

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

    def __repr__(self) -> str:
        repr_str = f"StandardLengthType(base_data_type='{self.base_data_type}', bit_length={self.bit_length}"
        if self.bit_mask is not None:
            repr_str += f", bit_mask={self.bit_mask}"
        if self.is_condensed_raw:
            repr_str += f", is_condensed_raw={self.is_condensed_raw}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()
