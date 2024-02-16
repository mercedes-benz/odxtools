# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Optional

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise
from .odxtypes import AtomicOdxType, DataType


@dataclass
class LeadingLengthInfoType(DiagCodedType):
    #: bit length of the length specifier field
    #:
    #: this is then followed by the number of bytes specified by that
    #: field, i.e., this is NOT the length of the LeadingLengthInfoType
    #: object.
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
        # note that self.bit_length is just the length of the length
        # specifier field. This is then followed by the same number of
        # bytes as the value of this field, i.e., the length of this
        # DCT is dynamic!
        return None

    def convert_internal_to_bytes(self, internal_value: Any, encode_state: EncodeState,
                                  bit_position: int) -> bytes:

        byte_length = self._minimal_byte_length_of(internal_value)

        length_bytes = self._encode_internal_value(
            byte_length,
            bit_position=bit_position,
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        value_bytes = self._encode_internal_value(
            internal_value,
            bit_position=0,
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        return length_bytes + value_bytes

    def decode_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:

        # Extract length of the parameter value
        byte_length = decode_state.extract_atomic_value(
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,  # length is an integer
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        if not isinstance(byte_length, int):
            odxraise()

        # Extract actual value
        # TODO: The returned value is None if the byte_length is 0. Maybe change it
        #       to some default value like an empty bytearray() or 0?
        value = decode_state.extract_atomic_value(
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        return value
