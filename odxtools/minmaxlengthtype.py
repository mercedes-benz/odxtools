# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert
from .odxtypes import DataType


@dataclass
class MinMaxLengthType(DiagCodedType):
    min_length: int
    max_length: Optional[int]
    termination: str

    def __post_init__(self):
        odxassert(self.max_length is None or self.min_length <= self.max_length)
        odxassert(
            self.base_data_type in [
                DataType.A_BYTEFIELD,
                DataType.A_ASCIISTRING,
                DataType.A_UNICODE2STRING,
                DataType.A_UTF8STRING,
            ], f"A min-max length type cannot have the base data type {self.base_data_type}.")
        odxassert(self.termination in [
            "ZERO",
            "HEX-FF",
            "END-OF-PDU",
        ], f"A min-max length type cannot have the termination {self.termination}")

    @property
    def dct_type(self) -> DctType:
        return "MIN-MAX-LENGTH-TYPE"

    def __termination_character(self):
        """Returns the termination character or None if it isn't defined."""
        # The termination character is actually not specified by ASAM
        # for A_BYTEFIELD but I assume it is only one byte.
        termination_char = None
        if self.termination == "ZERO":
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_char = bytes([0x0])
            else:
                termination_char = bytes([0x0, 0x0])
        elif self.termination == "HEX-FF":
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_char = bytes([0xFF])
            else:
                termination_char = bytes([0xFF, 0xFF])
        return termination_char

    def convert_internal_to_bytes(self, internal_value, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        byte_length = self._minimal_byte_length_of(internal_value)

        # The coded value must have at least length min_length
        if byte_length < self.min_length:
            raise EncodeError(f"The internal value {internal_value} is only {byte_length} bytes"
                              f" long but the min length is {self.min_length}")
        # The coded value must not have a length greater than max_length
        if self.max_length and byte_length > self.max_length:
            raise EncodeError(f"The internal value {internal_value} requires {byte_length}"
                              f" bytes, but the max length is {self.max_length}")

        value_byte = self._to_bytes(
            internal_value,
            bit_position=0,
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        if encode_state.is_end_of_pdu or byte_length == self.max_length:
            # All termination types may be ended by the PDU
            return value_byte
        else:
            termination_char = self.__termination_character()
            if self.termination == "END-OF-PDU":
                termination_char = bytes()
            odxassert(
                termination_char is not None,
                f"MinMaxLengthType with termination {self.termination}"
                f"(min: {self.min_length}, max: {self.max_length}) failed encoding {internal_value}"
            )
            return value_byte + termination_char

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        if decode_state.next_byte_position + self.min_length > len(decode_state.coded_message):
            raise DecodeError("The PDU ended before min length was reached.")

        coded_message = decode_state.coded_message
        byte_position = decode_state.next_byte_position
        termination_char = self.__termination_character()

        # If no termination char is found, this is the next byte after the parameter.
        max_termination_byte = len(coded_message)
        if self.max_length is not None:
            max_termination_byte = min(max_termination_byte, byte_position + self.max_length)

        if self.termination != "END-OF-PDU":
            # The parameter either ends after max length, at the end of the PDU
            # or if a termination character is found.
            char_length = len(termination_char)  # either 1 or 2

            termination_byte = byte_position + self.min_length
            found_char = False
            # Search the termination character
            while termination_byte < max_termination_byte and not found_char:
                found_char = (
                    coded_message[termination_byte:termination_byte +
                                  char_length] == termination_char)
                if not found_char:
                    termination_byte += char_length

            byte_length = termination_byte - byte_position

            # Extract the value
            value, byte = self._extract_internal(
                decode_state.coded_message,
                byte_position=byte_position,
                bit_position=bit_position,
                bit_length=8 * byte_length,
                base_data_type=self.base_data_type,
                is_highlow_byte_order=self.is_highlow_byte_order,
            )
            odxassert(byte == termination_byte)

            # next byte starts after the termination character
            next_byte_position = byte + char_length if found_char else byte
            return value, next_byte_position
        else:
            # If termination == "END-OF-PDU", the parameter ends after max_length
            # or at the end of the PDU.
            byte_length = max_termination_byte - byte_position

            value, byte = self._extract_internal(
                decode_state.coded_message,
                byte_position=byte_position,
                bit_position=bit_position,
                bit_length=8 * byte_length,
                base_data_type=self.base_data_type,
                is_highlow_byte_order=self.is_highlow_byte_order,
            )
            return value, byte
