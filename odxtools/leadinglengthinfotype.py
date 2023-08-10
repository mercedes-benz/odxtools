# SPDX-License-Identifier: MIT
from typing import Any, Optional

from .decodestate import DecodeState
from .diagcodedtype import DiagCodedType
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise
from .odxtypes import DataType


class LeadingLengthInfoType(DiagCodedType):

    def __init__(
        self,
        *,
        base_data_type: DataType,
        bit_length: int,
        base_type_encoding: Optional[str],
        is_highlow_byte_order_raw: Optional[bool],
    ):
        super().__init__(
            base_data_type=base_data_type,
            dct_type="LEADING-LENGTH-INFO-TYPE",
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw,
        )
        self.bit_length = bit_length
        odxassert(self.bit_length > 0,
                  "A Leading length info type with bit length == 0 does not make sense.")
        odxassert(
            self.base_data_type in [
                DataType.A_BYTEFIELD,
                DataType.A_ASCIISTRING,
                DataType.A_UNICODE2STRING,
                DataType.A_UTF8STRING,
            ], f"A leading length info type cannot have the base data type {self.base_data_type}.")

    def convert_internal_to_bytes(self, internal_value: Any, encode_state: EncodeState,
                                  bit_position: int) -> bytes:

        byte_length = self._minimal_byte_length_of(internal_value)

        length_byte = self._to_bytes(
            byte_length,
            bit_position=bit_position,
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        value_byte = self._to_bytes(
            internal_value,
            bit_position=0,
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        return length_byte + value_byte

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        coded_message = decode_state.coded_message

        # Extract length of the parameter value
        byte_length, byte_position = self._extract_internal(
            coded_message=coded_message,
            byte_position=decode_state.next_byte_position,
            bit_position=bit_position,
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,  # length is an integer
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        if not isinstance(byte_length, int):
            odxraise()

        # Extract actual value
        # TODO: The returned value is None if the byte_length is 0. Maybe change it
        #       to some default value like an empty bytearray() or 0?
        value, next_byte_position = self._extract_internal(
            coded_message=coded_message,
            byte_position=byte_position,
            bit_position=0,
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        return value, next_byte_position

    def __repr__(self) -> str:
        repr_str = f"LeadingLengthInfoType(base_data_type='{self.base_data_type}', bit_length={self.bit_length}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()
