# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass, field
from typing import Dict, Optional

from .exceptions import EncodeError, OdxWarning, odxassert, odxraise
from .odxtypes import AtomicOdxType, DataType

try:
    import bitstruct.c as bitstruct
except ImportError:
    import bitstruct


@dataclass
class EncodeState:
    """Utility class to holding the state variables needed for encoding a message.
    """

    #: payload that has been constructed so far
    coded_message: bytearray

    #: The absolute position in bytes from the beginning of the PDU to
    #: which relative positions refer to, e.g., the beginning of the
    #: structure.
    origin_byte_position: int = 0

    #: The absolute position in bytes from the beginning of the PDU
    #: where the next object ought to be placed into the PDU
    cursor_byte_position: int = 0

    #: The bit position [0-7] where the next object ought to be
    #: placed into the PDU
    cursor_bit_position: int = 0

    #: If encoding a response: request that triggered the response
    triggering_request: Optional[bytes] = None

    #: Mapping from the short name of a length-key parameter to bit
    #: lengths (specified by LengthKeyParameter)
    length_keys: Dict[str, int] = field(default_factory=dict)

    #: Mapping from the short name of a table-key parameter to the
    #: short name of the corresponding row of the table (specified by
    #: TableKeyParameter)
    table_keys: Dict[str, str] = field(default_factory=dict)

    #: The cursor position where a given length- or table key is located
    #: in the PDU
    key_pos: Dict[str, int] = field(default_factory=dict)

    #: Flag whether we are currently the last parameter of the PDU
    #: (needed for MinMaxLengthType, EndOfPduField, etc.)
    is_end_of_pdu: bool = True

    def emplace_atomic_value(
        self,
        *,
        internal_value: AtomicOdxType,
        bit_length: int,
        base_data_type: DataType,
        is_highlow_byte_order: bool,
    ) -> None:
        """Convert the internal_value to bytes and emplace this into the PDU"""
        # Check that bytes and strings actually fit into the bit length
        if base_data_type == DataType.A_BYTEFIELD:
            if isinstance(internal_value, bytearray):
                internal_value = bytes(internal_value)
            if not isinstance(internal_value, bytes):
                odxraise()
            if 8 * len(internal_value) > bit_length:
                raise EncodeError(f"The bytefield {internal_value.hex()} is too large "
                                  f"({len(internal_value)} bytes)."
                                  f" The maximum length is {bit_length//8}.")
        if base_data_type == DataType.A_ASCIISTRING:
            if not isinstance(internal_value, str):
                odxraise()

            # The spec says ASCII, meaning only byte values 0-127.
            # But in practice, vendors use iso-8859-1, aka latin-1
            # reason being iso-8859-1 never fails since it has a valid
            # character mapping for every possible byte sequence.
            internal_value = internal_value.encode("iso-8859-1")

            if 8 * len(internal_value) > bit_length:
                raise EncodeError(f"The string {repr(internal_value)} is too large."
                                  f" The maximum number of characters is {bit_length//8}.")
        elif base_data_type == DataType.A_UTF8STRING:
            if not isinstance(internal_value, str):
                odxraise()

            internal_value = internal_value.encode("utf-8")

            if 8 * len(internal_value) > bit_length:
                raise EncodeError(f"The string {repr(internal_value)} is too large."
                                  f" The maximum number of bytes is {bit_length//8}.")

        elif base_data_type == DataType.A_UNICODE2STRING:
            if not isinstance(internal_value, str):
                odxraise()

            text_encoding = "utf-16-be" if is_highlow_byte_order else "utf-16-le"
            internal_value = internal_value.encode(text_encoding)

            if 8 * len(internal_value) > bit_length:
                raise EncodeError(f"The string {repr(internal_value)} is too large."
                                  f" The maximum number of characters is {bit_length//16}.")

        # If the bit length is zero, return empty bytes
        if bit_length == 0:
            if (base_data_type.value in [
                    DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64
            ] and base_data_type.value != 0):
                odxraise(
                    f"The number {repr(internal_value)} cannot be encoded into {bit_length} bits.",
                    EncodeError)
            self.emplace_bytes(b'')
            return

        char = base_data_type.bitstruct_format_letter
        padding = (8 - ((bit_length + self.cursor_bit_position) % 8)) % 8
        odxassert((0 <= padding and padding < 8 and
                   (padding + bit_length + self.cursor_bit_position) % 8 == 0),
                  f"Incorrect padding {padding}")
        left_pad = f"p{padding}" if padding > 0 else ""

        # actually encode the value
        coded = bitstruct.pack(f"{left_pad}{char}{bit_length}", internal_value)

        # apply byte order for numeric objects
        if not is_highlow_byte_order and base_data_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
                DataType.A_FLOAT32,
                DataType.A_FLOAT64,
        ]:
            coded = coded[::-1]

        self.emplace_bytes(coded)

    def emplace_bytes(self, new_data: bytes, obj_name: Optional[str] = None) -> None:
        pos = self.cursor_byte_position

        # Make blob longer if necessary
        min_length = pos + len(new_data)
        if len(self.coded_message) < min_length:
            self.coded_message.extend([0] * (min_length - len(self.coded_message)))

        for i in range(len(new_data)):
            # insert new byte. this is pretty hacky: it will fail if
            # the value to be inserted is bitwise "disjoint" from the
            # value which is already in the PDU...
            if self.coded_message[pos + i] & new_data[i] != 0:
                if obj_name is not None:
                    warnings.warn(
                        f"'{obj_name}' overlaps with another object (bits to be set are already set)",
                        OdxWarning,
                        stacklevel=1,
                    )
                else:
                    warnings.warn(
                        "Object overlap (bits to be set are already set)",
                        OdxWarning,
                        stacklevel=1,
                    )

            self.coded_message[pos + i] |= new_data[i]

        self.cursor_byte_position += len(new_data)
        self.cursor_bit_position = 0
