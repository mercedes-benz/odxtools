# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional, Tuple

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise
from .odxtypes import AtomicOdxType, DataType


@dataclass
class MinMaxLengthType(DiagCodedType):
    min_length: int
    max_length: Optional[int]
    termination: str

    def __post_init__(self) -> None:
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

    def __termination_sequence(self) -> bytes:
        """Returns the termination byte sequence if it isn't defined."""
        # The termination sequence is actually not specified by ASAM
        # for A_BYTEFIELD but I assume it is only one byte.
        termination_sequence = b''
        if self.termination == "ZERO":
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_sequence = bytes([0x0])
            else:
                termination_sequence = bytes([0x0, 0x0])
        elif self.termination == "HEX-FF":
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_sequence = bytes([0xFF])
            else:
                termination_sequence = bytes([0xFF, 0xFF])
        return termination_sequence

    def convert_internal_to_bytes(self, internal_value: AtomicOdxType, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        if not isinstance(internal_value, (bytes, str)):
            odxraise("MinMaxLengthType is currently only implemented for strings and byte arrays",
                     EncodeError)

        if self.max_length is not None:
            data_length = min(len(internal_value), self.max_length)
        else:
            data_length = len(internal_value)

        value_bytes = bytearray(
            self._to_bytes(
                internal_value,
                bit_position=0,
                bit_length=8 * data_length,
                base_data_type=self.base_data_type,
                is_highlow_byte_order=self.is_highlow_byte_order,
            ))

        # TODO: ensure that the termination delimiter is not
        # encountered within the encoded value.

        odxassert(self.termination != "END-OF-PDU" or encode_state.is_end_of_pdu)
        if encode_state.is_end_of_pdu or len(value_bytes) == self.max_length:
            # All termination types may be ended by the end of the PDU
            # or once reaching the maximum length. In this case, we
            # must not add the termination sequence
            pass
        else:
            termination_sequence = self.__termination_sequence()

            # ensure that we don't try to encode an odd-length
            # value when using a two-byte terminator
            odxassert(len(value_bytes) % len(termination_sequence) == 0)

            value_bytes.extend(termination_sequence)

        if len(value_bytes) < self.min_length:
            raise EncodeError(f"Encoded value for MinMaxLengthType "
                              f"must be at least {self.min_length} bytes long. "
                              f"(Is: {len(value_bytes)} bytes.)")
        elif self.max_length is not None and len(value_bytes) > self.max_length:
            raise EncodeError(f"Encoded value for MinMaxLengthType "
                              f"must not be longer than {self.max_length} bytes. "
                              f"(Is: {len(value_bytes)} bytes.)")

        return value_bytes

    def convert_bytes_to_internal(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[AtomicOdxType, int]:
        if decode_state.cursor_position + self.min_length > len(decode_state.coded_message):
            raise DecodeError("The PDU ended before minimum length was reached.")

        coded_message = decode_state.coded_message
        cursor_pos = decode_state.cursor_position
        termination_seq = self.__termination_sequence()

        max_terminator_pos = len(coded_message)
        if self.max_length is not None:
            max_terminator_pos = min(max_terminator_pos, cursor_pos + self.max_length)

        if self.termination != "END-OF-PDU":
            # The parameter either ends after the maximum length, at
            # the end of the PDU or if a termination sequence is
            # found.

            terminator_pos = cursor_pos + self.min_length
            while True:
                # Search the termination sequence
                terminator_pos = coded_message.find(termination_seq, terminator_pos,
                                                    max_terminator_pos)
                if terminator_pos < 0:
                    # termination sequence was not found, i.e., we
                    # are terminated by either the end of the PDU or
                    # our maximum size. (whatever is the smaller
                    # value.)
                    byte_length = max_terminator_pos - cursor_pos
                    break
                elif (terminator_pos - cursor_pos) % len(termination_seq) == 0:
                    # we found the termination sequence at a position
                    # and it is correctly aligned (two-byte
                    # termination sequences must be word aligned
                    # relative to the beginning of the parameter)!
                    byte_length = terminator_pos - cursor_pos
                    break
                else:
                    # we found the termination sequence, but its
                    # alignment was incorrect. Try again one byte
                    # further...
                    terminator_pos += 1

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
                byte_pos += len(termination_seq)

            # next byte starts after the actual data and the termination sequence
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
