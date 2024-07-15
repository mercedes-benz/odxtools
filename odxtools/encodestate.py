# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, SupportsBytes, Tuple

from .exceptions import EncodeError, OdxWarning, odxassert, odxraise
from .odxtypes import AtomicOdxType, DataType, ParameterValue

try:
    import bitstruct.c as bitstruct
except ImportError:
    import bitstruct

if TYPE_CHECKING:
    from .parameters.parameter import Parameter


@dataclass
class EncodeState:
    """Utility class to holding the state variables needed for encoding a message.
    """

    #: payload that has been constructed so far
    coded_message: bytearray = field(default_factory=bytearray)

    #: the bits of the payload that are used
    used_mask: bytearray = field(default_factory=bytearray)

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

    #: list of parameters that have been encoded so far. The journal
    #: is used by some types of parameters which depend on the values of
    #: other parameters; e.g., environment data description parameters
    journal: List[Tuple["Parameter", Optional[ParameterValue]]] = field(default_factory=list)

    #: If this is True, specifying unknown parameters for encoding
    #: will raise an OdxError exception in strict mode.
    allow_unknown_parameters = False

    def __post_init__(self) -> None:
        # if a coded message has been specified, but no used_mask, we
        # assume that all of the bits of the coded message are
        # currently used.
        if len(self.coded_message) > len(self.used_mask):
            self.used_mask += b'\xff' * (len(self.coded_message) - len(self.used_mask))
        if len(self.coded_message) < len(self.used_mask):
            odxraise(f"The specified bit mask 0x{self.used_mask.hex()} for used bits "
                     f"is not suitable for representing the coded_message "
                     f"0x{self.coded_message.hex()}")
            self.used_mask = self.used_mask[:len(self.coded_message)]

    def emplace_atomic_value(
        self,
        *,
        internal_value: AtomicOdxType,
        bit_length: int,
        base_data_type: DataType,
        is_highlow_byte_order: bool,
        used_mask: Optional[bytes],
    ) -> None:
        """Convert the internal_value to bytes and emplace this into the PDU"""

        raw_value: AtomicOdxType

        # Check that bytes and strings actually fit into the bit length
        if base_data_type == DataType.A_BYTEFIELD:
            if not isinstance(internal_value, (bytes, bytearray, SupportsBytes)):
                odxraise()
            if 8 * len(internal_value) > bit_length:
                raise EncodeError(f"The bytefield {internal_value.hex()} is too large "
                                  f"({len(internal_value)} bytes)."
                                  f" The maximum length is {bit_length//8}.")
            raw_value = bytes(internal_value)
        elif base_data_type == DataType.A_ASCIISTRING:
            if not isinstance(internal_value, str):
                odxraise()

            # The spec says ASCII, meaning only byte values 0-127.
            # But in practice, vendors use iso-8859-1, aka latin-1
            # reason being iso-8859-1 never fails since it has a valid
            # character mapping for every possible byte sequence.
            raw_value = internal_value.encode("iso-8859-1")

            if 8 * len(raw_value) > bit_length:
                raise EncodeError(f"The string {repr(internal_value)} is too large."
                                  f" The maximum number of characters is {bit_length//8}.")
        elif base_data_type == DataType.A_UTF8STRING:
            if not isinstance(internal_value, str):
                odxraise()

            raw_value = internal_value.encode("utf-8")

            if 8 * len(raw_value) > bit_length:
                raise EncodeError(f"The string {repr(internal_value)} is too large."
                                  f" The maximum number of bytes is {bit_length//8}.")

        elif base_data_type == DataType.A_UNICODE2STRING:
            if not isinstance(internal_value, str):
                odxraise()

            text_encoding = "utf-16-be" if is_highlow_byte_order else "utf-16-le"
            raw_value = internal_value.encode(text_encoding)

            if 8 * len(raw_value) > bit_length:
                raise EncodeError(f"The string {repr(internal_value)} is too large."
                                  f" The maximum number of characters is {bit_length//16}.")
        else:
            raw_value = internal_value

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
        coded = bitstruct.pack(f"{left_pad}{char}{bit_length}", raw_value)

        # create the raw mask of used bits for numeric objects
        used_mask_raw = used_mask
        if base_data_type in [DataType.A_INT32, DataType.A_UINT32
                             ] and (self.cursor_bit_position != 0 or
                                    (self.cursor_bit_position + bit_length) % 8 != 0):
            if used_mask is None:
                tmp = (1 << bit_length) - 1
            else:
                tmp = int.from_bytes(used_mask, "big")
            tmp <<= self.cursor_bit_position

            used_mask_raw = tmp.to_bytes((self.cursor_bit_position + bit_length + 7) // 8, "big")

        # apply byte order to numeric objects
        if not is_highlow_byte_order and base_data_type in [
                DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64
        ]:
            coded = coded[::-1]

            if used_mask_raw is not None:
                used_mask_raw = used_mask_raw[::-1]

        self.cursor_bit_position = 0
        self.emplace_bytes(coded, obj_used_mask=used_mask_raw)

    def emplace_bytes(self,
                      new_data: bytes,
                      obj_name: Optional[str] = None,
                      obj_used_mask: Optional[bytes] = None) -> None:
        if self.cursor_bit_position != 0:
            odxraise("EncodeState.emplace_bytes can only be called "
                     "for a bit position of 0!", RuntimeError)

        pos = self.cursor_byte_position

        # Make blob longer if necessary
        min_length = pos + len(new_data)
        if len(self.coded_message) < min_length:
            pad = b'\x00' * (min_length - len(self.coded_message))
            self.coded_message += pad
            self.used_mask += pad

        if obj_used_mask is None:
            # Happy path for when no obj_used_mask has been
            # specified. In this case we assume that all bits of the
            # new data to be emplaced are used.
            n = len(new_data)

            if self.used_mask[pos:pos + n] != b'\x00' * n:
                warnings.warn(
                    f"Overlapping objects detected in between bytes {pos} and "
                    f"{pos+n}",
                    OdxWarning,
                    stacklevel=1,
                )
            self.coded_message[pos:pos + n] = new_data
            self.used_mask[pos:pos + n] = b'\xff' * n
        else:
            # insert data the hard way, i.e. we have to look at each
            # individual byte to determine if it has already been used
            # somewhere else (it would be nice if bytearrays supported
            # bitwise operations!)
            for i in range(len(new_data)):
                if self.used_mask[pos + i] & obj_used_mask[i] != 0:
                    warnings.warn(
                        f"Overlapping objects detected at position {pos + i}",
                        OdxWarning,
                        stacklevel=1,
                    )
                self.coded_message[pos + i] &= ~obj_used_mask[i]
                self.coded_message[pos + i] |= new_data[i] & obj_used_mask[i]
                self.used_mask[pos + i] |= obj_used_mask[i]

        self.cursor_byte_position += len(new_data)
