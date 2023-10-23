# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise
from .odxtypes import AtomicOdxType, DataType


@dataclass
class LeadingLengthInfoType(DiagCodedType):
    bit_length: int

    def __post_init__(self) -> None:
        odxassert(self.bit_length > 0,
                  "A Leading length info type with bit length == 0 does not make sense.")
        odxassert(
            self.base_data_type in [
                DataType.A_BYTEFIELD,
                DataType.A_ASCIISTRING,
                DataType.A_UNICODE2STRING,
                DataType.A_UTF8STRING,
            ],
            f"A leading length info type cannot have the base data type {self.base_data_type.name}."
        )

    @property
    def dct_type(self) -> DctType:
        return "LEADING-LENGTH-INFO-TYPE"

    def get_static_bit_length(self) -> Optional[int]:
        return self.bit_length

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

    def convert_bytes_to_internal(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[AtomicOdxType, int]:
        coded_message = decode_state.coded_message

        # Extract length of the parameter value
        byte_length, byte_position = self._extract_internal(
            coded_message=coded_message,
            byte_position=decode_state.cursor_position,
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
        value, cursor_position = self._extract_internal(
            coded_message=coded_message,
            byte_position=byte_position,
            bit_position=0,
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        return value, cursor_position
