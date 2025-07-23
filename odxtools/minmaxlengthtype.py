# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .encoding import get_string_encoding
from .exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxtypes import AtomicOdxType, BytesTypes, DataType
from .termination import Termination
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class MinMaxLengthType(DiagCodedType):
    max_length: int | None = None
    min_length: int
    termination: Termination

    @property
    def dct_type(self) -> DctType:
        return "MIN-MAX-LENGTH-TYPE"

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MinMaxLengthType":
        kwargs = dataclass_fields_asdict(DiagCodedType.from_et(et_element, context))

        max_length = None
        if et_element.find("MAX-LENGTH") is not None:
            max_length = int(odxrequire(et_element.findtext("MAX-LENGTH")))
        min_length = int(odxrequire(et_element.findtext("MIN-LENGTH")))

        termination_str = odxrequire(et_element.attrib.get("TERMINATION"))
        try:
            termination = Termination(termination_str)
        except ValueError:
            termination = cast(Termination, None)
            odxraise(f"Encountered unknown termination type '{termination_str}'")

        return MinMaxLengthType(
            max_length=max_length, min_length=min_length, termination=termination, **kwargs)

    def __post_init__(self) -> None:
        odxassert(self.max_length is None or self.min_length <= self.max_length)
        odxassert(
            self.base_data_type in [
                DataType.A_BYTEFIELD,
                DataType.A_ASCIISTRING,
                DataType.A_UNICODE2STRING,
                DataType.A_UTF8STRING,
            ], f"A min-max length type cannot have the base data type {self.base_data_type}.")

    def __termination_sequence(self) -> bytes:
        """Returns the termination byte sequence if it isn't defined."""
        # The termination sequence is actually not specified by ASAM
        # for A_BYTEFIELD but I assume it is only one byte.
        termination_sequence = b''
        if self.termination == Termination.ZERO:
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_sequence = bytes([0x0])
            else:
                termination_sequence = bytes([0x0, 0x0])
        elif self.termination == Termination.HEX_FF:
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_sequence = bytes([0xFF])
            else:
                termination_sequence = bytes([0xFF, 0xFF])
        return termination_sequence

    @override
    def encode_into_pdu(self, internal_value: AtomicOdxType, encode_state: EncodeState) -> None:

        if not isinstance(internal_value, (str, BytesTypes)):
            odxraise("MinMaxLengthType is currently only implemented for strings and byte arrays",
                     EncodeError)

        raw_value = b''
        if isinstance(internal_value, str):
            str_encoding = get_string_encoding(self.base_data_type, self.base_type_encoding,
                                               self.is_highlow_byte_order)

            if str_encoding is None:
                odxraise(f"Internal string value specified for object which is "
                         f"'{self.base_data_type.value}' not a string")
                raw_value = b''
            else:
                raw_value = internal_value.encode(str_encoding)
        else:
            raw_value = bytes(internal_value)

        data_length = len(raw_value)

        if data_length < self.min_length:
            odxraise(
                f"Encoded value for MinMaxLengthType "
                f"must be at least {self.min_length} bytes long. "
                f"(Is: {data_length} bytes.)", EncodeError)
            data_length = self.min_length
        elif self.max_length is not None and data_length > self.max_length:
            odxraise(
                f"Encoded value for MinMaxLengthType "
                f"must not be longer than {self.max_length} bytes. "
                f"(Is: {data_length} bytes.)", EncodeError)
            data_length = self.max_length

        encode_state.emplace_atomic_value(
            internal_value=raw_value,
            used_mask=None,
            bit_length=8 * data_length,
            base_data_type=DataType.A_BYTEFIELD,
            base_type_encoding=None,
            is_highlow_byte_order=True,
        )

        # TODO: ensure that the termination delimiter is not
        # encountered within the encoded value.

        odxassert(
            self.termination != Termination.END_OF_PDU or encode_state.is_end_of_pdu,
            "Encountered a MIN-MAX-LENGTH type with END-OF-PDU termination "
            "which is not located at the end of the PDU")
        if encode_state.is_end_of_pdu or data_length == self.max_length:
            # All termination types may be ended by the end of the PDU
            # or once reaching the maximum length. In this case, we
            # must not add the termination sequence
            pass
        else:
            termination_sequence = self.__termination_sequence()

            # ensure that we don't try to encode an odd-length
            # value when using a two-byte terminator
            odxassert(data_length % len(termination_sequence) == 0)

            data_length += len(termination_sequence)
            encode_state.emplace_bytes(termination_sequence)

    def decode_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        odxassert(decode_state.cursor_bit_position == 0,
                  "No bit position can be specified for MIN-MAX-LENGTH-TYPE values.")
        if decode_state.cursor_byte_position + self.min_length > len(decode_state.coded_message):
            raise DecodeError("The PDU ended before minimum length was reached.")

        coded_message = decode_state.coded_message
        orig_cursor_pos = decode_state.cursor_byte_position
        termination_seq = self.__termination_sequence()

        max_terminator_pos = len(coded_message)
        if self.max_length is not None:
            max_terminator_pos = min(max_terminator_pos, orig_cursor_pos + self.max_length)

        if self.termination != Termination.END_OF_PDU:
            # The parameter either ends after the maximum length, at
            # the end of the PDU or if a termination sequence is
            # found.

            # Find the location of the termination sequence. The
            # problem here is that the alignment of the termination
            # sequence must be correct for it to be a termination
            # sequence. (e.g., an odd-aligned double-zero for UTF-16
            # strings is *not* a termination sequence!)
            terminator_pos = orig_cursor_pos + self.min_length
            while True:
                terminator_pos = decode_state.coded_message.find(termination_seq, terminator_pos,
                                                                 max_terminator_pos)
                if terminator_pos < 0:
                    # termination sequence was not found, i.e., we
                    # are terminated by either the end of the PDU or
                    # our maximum size. (whatever is the smaller
                    # value.)
                    byte_length = max_terminator_pos - orig_cursor_pos
                    break
                elif (terminator_pos - orig_cursor_pos) % len(termination_seq) == 0:
                    # we found the termination sequence at a position
                    # and it is correctly aligned (two-byte
                    # termination sequences must be word aligned
                    # relative to the beginning of the parameter)!
                    byte_length = terminator_pos - orig_cursor_pos
                    break
                else:
                    # we found the termination sequence, but its
                    # alignment was incorrect. Try again one byte
                    # further...
                    terminator_pos += 1

            # Extract the value
            value = decode_state.extract_atomic_value(
                bit_length=8 * byte_length,
                base_data_type=self.base_data_type,
                base_type_encoding=self.base_type_encoding,
                is_highlow_byte_order=self.is_highlow_byte_order,
            )

            if decode_state.cursor_byte_position != len(
                    decode_state.coded_message
            ) and decode_state.cursor_byte_position - orig_cursor_pos != self.max_length:
                # next object starts after the actual data and the termination sequence
                decode_state.cursor_byte_position += len(termination_seq)

            return value
        else:
            # If termination == "END-OF-PDU", the parameter ends after max_length
            # or at the end of the PDU.
            byte_length = max_terminator_pos - orig_cursor_pos

            value = decode_state.extract_atomic_value(
                bit_length=8 * byte_length,
                base_data_type=self.base_data_type,
                base_type_encoding=self.base_type_encoding,
                is_highlow_byte_order=self.is_highlow_byte_order,
            )

            return value
