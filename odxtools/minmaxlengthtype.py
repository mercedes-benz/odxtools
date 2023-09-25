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

    def __termination_character(self) -> bytes:
        """Returns the termination character or None if it isn't defined."""
        # The termination character is actually not specified by ASAM
        # for A_BYTEFIELD but I assume it is only one byte.
        termination_char = b''
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
        bit_length = 8 * self.max_length if self.max_length is not None else 8 * len(internal_value)
        bit_length = min(8 * len(internal_value), bit_length)
        value_bytes = bytearray(
            self._to_bytes(
                internal_value,
                bit_position=0,
                bit_length=bit_length,
                base_data_type=self.base_data_type,
                is_highlow_byte_order=self.is_highlow_byte_order,
            ))

        # TODO: ensure that the termination delimiter is not
        # encountered within the encoded value.

        if encode_state.is_end_of_pdu or len(value_bytes) == self.max_length:
            # All termination types may be ended by the end of the PDU
            # or once reaching the maximum length. In this case, we
            # must not add the termination character
            pass
        else:
            termination_char = self.__termination_character()
            if termination_char is not None:
                # ensure that we don't try to encode an odd-length
                # value whn using a two-character terminator
                odxassert(len(value_bytes) % len(termination_char) == 0)

                value_bytes.extend(termination_char)

        if len(value_bytes) < self.min_length:
            raise EncodeError(f"Encoded value for MinMaxLengthType "
                              f"must be at least {self.min_length} bytes long. "
                              f"(Is: {len(value_bytes)} bytes.)")
        elif self.max_length is not None and len(value_bytes) > self.max_length:
            raise EncodeError(f"Encoded value for MinMaxLengthType "
                              f"must not be longer than {self.max_length} bytes. "
                              f"(Is: {len(value_bytes)} bytes.)")

        return value_bytes

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        if decode_state.cursor_position + self.min_length > len(decode_state.coded_message):
            raise DecodeError("The PDU ended before minimum length was reached.")

        coded_message = decode_state.coded_message
        cursor_pos = decode_state.cursor_position
        terminator_char = self.__termination_character()

        # If no termination char is found, this is the next byte after the parameter.
        max_terminator_pos = len(coded_message)
        if self.max_length is not None:
            max_terminator_pos = min(max_terminator_pos, cursor_pos + self.max_length)

        if self.termination != "END-OF-PDU":
            # The parameter either ends after the maximum length, at
            # the end of the PDU or if a termination character is
            # found.

            terminator_pos = cursor_pos + self.min_length
            while True:
                # Search the termination character
                terminator_pos = coded_message.find(terminator_char, terminator_pos,
                                                    max_terminator_pos)
                if terminator_pos < 0:
                    # termination character was not found, i.e., we
                    # are terminated by either the end of the PDU or
                    # our maximum size. (whatever is the smaller
                    # value.)
                    terminator_pos = len(coded_message)
                    if self.max_length is not None:
                        terminator_pos = min(cursor_pos + self.max_length, terminator_pos)

                    byte_length = terminator_pos - cursor_pos
                    break
                elif (terminator_pos - cursor_pos) % len(terminator_char) == 0:
                    # we found the termination character at a position
                    # and it is correctly aligned (two-byte
                    # termination "characters" must be word aligned
                    # relative to the beginning of the parameter)!
                    byte_length = terminator_pos - cursor_pos
                    break
                else:
                    # we found the termination character, but its
                    # alignment was incorrect. Try again one byte
                    # further...
                    terminator_pos += 1

            if byte_length < self.min_length:
                raise DecodeError(f"MinMaxLengthType must be more than {self.min_length} "
                                  f"bytes long. (Is: {byte_length} bytes)")
            if self.max_length is not None and byte_length > self.max_length:
                raise DecodeError(f"MinMaxLengthType must be at most {self.max_length} "
                                  f"bytes long. (Is: {byte_length} bytes)")

            # Extract the value
            value, byte_pos = self._extract_internal(
                decode_state.coded_message,
                byte_position=cursor_pos,
                bit_position=bit_position,
                bit_length=8 * byte_length,
                base_data_type=self.base_data_type,
                is_highlow_byte_order=self.is_highlow_byte_order,
            )

            if byte_pos != len(coded_message) and byte_pos - cursor_pos != self.max_length:
                byte_pos += len(terminator_char)

            # next byte starts after the actual data and the termination character
            return value, byte_pos
        else:
            # If termination == "END-OF-PDU", the parameter ends after max_length
            # or at the end of the PDU.
            byte_length = max_terminator_pos - cursor_pos

            value, byte_pos = self._extract_internal(
                decode_state.coded_message,
                byte_position=cursor_pos,
                bit_position=bit_position,
                bit_length=8 * byte_length,
                base_data_type=self.base_data_type,
                is_highlow_byte_order=self.is_highlow_byte_order,
            )
            return value, byte_pos
