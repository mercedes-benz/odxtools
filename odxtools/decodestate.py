# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict

import odxtools.exceptions as exceptions

from .exceptions import DecodeError
from .odxtypes import AtomicOdxType, DataType

try:
    import bitstruct.c as bitstruct
except ImportError:
    import bitstruct

if TYPE_CHECKING:
    from .tablerow import TableRow

# format specifiers for the data type using the bitstruct module
ODX_TYPE_TO_FORMAT_LETTER = {
    DataType.A_INT32: "s",
    DataType.A_UINT32: "u",
    DataType.A_FLOAT32: "f",
    DataType.A_FLOAT64: "f",
    DataType.A_BYTEFIELD: "r",
    DataType.A_UNICODE2STRING: "r",  # UTF-16 strings must be converted explicitly
    DataType.A_ASCIISTRING: "r",
    DataType.A_UTF8STRING: "r",
}


@dataclass
class DecodeState:
    """Utility class to be used while decoding a message."""

    #: bytes to be decoded
    coded_message: bytes

    #: Absolute position of the origin
    #:
    #: i.e., the absolute byte position to which all relative positions
    #: refer to, e.g. the position of the first byte of a structure.
    origin_byte_position: int = 0

    #: Absolute position of the next undecoded byte to be considered
    #:
    #: (if not explicitly specified by the object to be decoded.)
    cursor_byte_position: int = 0

    #: the bit position [0, 7] where the object to be extracted begins
    #:
    #: If bit position is undefined (`None`), the object to be extracted
    #: starts at bit 0.
    cursor_bit_position: int = 0

    #: values of the length key parameters decoded so far
    length_keys: Dict[str, int] = field(default_factory=dict)

    #: values of the table key parameters decoded so far
    table_keys: Dict[str, "TableRow"] = field(default_factory=dict)

    def extract_atomic_value(
        self,
        bit_length: int,
        base_data_type: DataType,
        is_highlow_byte_order: bool,
    ) -> AtomicOdxType:
        """Extract an internal value from a blob of raw bytes.

        :return: Tuple with the internal value of the object and the
                 byte position of the first undecoded byte after the
                 extracted object.
        """
        # If the bit length is zero, return "empty" values of each type
        if bit_length == 0:
            return base_data_type.as_python_type()()

        byte_length = (bit_length + self.cursor_bit_position + 7) // 8
        if self.cursor_byte_position + byte_length > len(self.coded_message):
            raise DecodeError(f"Expected a longer message.")
        extracted_bytes = self.coded_message[self.cursor_byte_position:self.cursor_byte_position +
                                             byte_length]

        # Apply byteorder for numerical objects. Note that doing this
        # here might lead to garbage data being included in the result
        # if the data to be extracted is not byte aligned and crosses
        # byte boundaries, but it is what the specification says.
        if not is_highlow_byte_order and base_data_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
                DataType.A_FLOAT32,
                DataType.A_FLOAT64,
        ]:
            extracted_bytes = extracted_bytes[::-1]

        padding = (8 - (bit_length + self.cursor_bit_position) % 8) % 8
        internal_value, = bitstruct.unpack_from(
            f"{ODX_TYPE_TO_FORMAT_LETTER[base_data_type]}{bit_length}",
            extracted_bytes,
            offset=padding)

        text_errors = 'strict' if exceptions.strict_mode else 'replace'
        if base_data_type == DataType.A_ASCIISTRING:
            # The spec says ASCII, meaning only byte values 0-127.
            # But in practice, vendors use iso-8859-1, aka latin-1
            # reason being iso-8859-1 never fails since it has a valid
            # character mapping for every possible byte sequence.
            text_encoding = 'iso-8859-1'
            internal_value = internal_value.decode(encoding=text_encoding, errors=text_errors)
        elif base_data_type == DataType.A_UTF8STRING:
            text_encoding = "utf-8"
            internal_value = internal_value.decode(encoding=text_encoding, errors=text_errors)
        elif base_data_type == DataType.A_UNICODE2STRING:
            # For UTF-16, we need to manually decode the extracted
            # bytes to a string
            text_encoding = "utf-16-be" if is_highlow_byte_order else "utf-16-le"
            internal_value = internal_value.decode(encoding=text_encoding, errors=text_errors)

        self.cursor_byte_position += byte_length
        self.cursor_bit_position = 0

        return internal_value
