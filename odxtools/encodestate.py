# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .encoding import Encoding, get_string_encoding
from .exceptions import EncodeError, OdxWarning, odxassert, odxraise
from .odxtypes import AtomicOdxType, BytesTypes, DataType, ParameterValue

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
    triggering_request: bytes | None = None

    #: Mapping from the short name of a length-key parameter to bit
    #: lengths (specified by LengthKeyParameter)
    length_keys: dict[str, int] = field(default_factory=dict)

    #: Mapping from the short name of a table-key parameter to the
    #: short name of the corresponding row of the table (specified by
    #: TableKeyParameter)
    table_keys: dict[str, str] = field(default_factory=dict)

    #: The cursor position where a given length- or table key is located
    #: in the PDU
    key_pos: dict[str, int] = field(default_factory=dict)

    #: Flag whether we are currently the last parameter of the PDU
    #: (needed for MinMaxLengthType, EndOfPduField, etc.)
    is_end_of_pdu: bool = True

    #: list of parameters that have been encoded so far. The journal
    #: is used by some types of parameters which depend on the values of
    #: other parameters; e.g., environment data description parameters
    journal: list[tuple["Parameter", ParameterValue | None]] = field(default_factory=list)

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
        base_type_encoding: Encoding | None,
        is_highlow_byte_order: bool,
        used_mask: bytes | None,
    ) -> None:
        """Convert the internal_value to bytes and emplace this into the PDU"""

        raw_value: AtomicOdxType

        # Deal with raw byte fields, ...
        if base_data_type == DataType.A_BYTEFIELD:
            if not isinstance(internal_value, BytesTypes):
                odxraise(f"{internal_value!r} is not a bytefield", EncodeError)
                return

            odxassert(
                base_type_encoding in (None, Encoding.NONE, Encoding.BCD_P, Encoding.BCD_UP),
                f"Illegal encoding '{base_type_encoding}' for A_BYTEFIELD")

            # note that we do not ensure that BCD-encoded byte fields
            # only represent "legal" values
            raw_value = bytes(internal_value)

            if 8 * len(raw_value) > bit_length:
                odxraise(
                    f"The value '{internal_value!r}' cannot be encoded using "
                    f"{bit_length} bits.", EncodeError)
                raw_value = raw_value[0:bit_length // 8]

        # ... string types, ...
        elif base_data_type in (DataType.A_UTF8STRING, DataType.A_ASCIISTRING,
                                DataType.A_UNICODE2STRING):
            if not isinstance(internal_value, str):
                odxraise(f"The internal value '{internal_value!r}' is not a string", EncodeError)
                internal_value = str(internal_value)

            str_encoding = get_string_encoding(base_data_type, base_type_encoding,
                                               is_highlow_byte_order)
            if str_encoding is not None:
                raw_value = internal_value.encode(str_encoding)
            else:
                raw_value = b""

            if 8 * len(raw_value) > bit_length:
                odxraise(
                    f"The value '{internal_value!r}' cannot be encoded using "
                    f"{bit_length} bits.", EncodeError)
                raw_value = raw_value[0:bit_length // 8]

        # ... signed integers, ...
        elif base_data_type == DataType.A_INT32:
            if not isinstance(internal_value, int):
                odxraise(
                    f"Internal value must be of integer type, not {type(internal_value).__name__}",
                    EncodeError)
                internal_value = int(internal_value)

            if base_type_encoding == Encoding.ONEC:
                # one-complement
                if internal_value >= 0:
                    raw_value = internal_value
                else:
                    mask = (1 << bit_length) - 1
                    raw_value = mask + internal_value
            elif base_type_encoding in (None, Encoding.TWOC):
                # two-complement
                if internal_value >= 0:
                    raw_value = internal_value
                else:
                    mask = (1 << bit_length) - 1
                    raw_value = mask + internal_value + 1
            elif base_type_encoding == Encoding.SM:
                # sign-magnitude
                if internal_value >= 0:
                    raw_value = internal_value
                else:
                    raw_value = (1 << (bit_length - 1)) + abs(internal_value)
            else:
                odxraise(
                    f"Illegal encoding ({base_type_encoding and base_type_encoding.value}) specified for "
                    f"{base_data_type.value}")

                if base_type_encoding == Encoding.BCD_P:
                    raw_value = self.__encode_bcd_p(abs(internal_value))
                elif base_type_encoding == Encoding.BCD_UP:
                    raw_value = self.__encode_bcd_up(abs(internal_value))
                else:
                    raw_value = internal_value

            if raw_value.bit_length() > bit_length:
                odxraise(
                    f"The value '{internal_value!r}' cannot be encoded using "
                    f"{bit_length} bits.", EncodeError)
                raw_value &= (1 << bit_length) - 1

        # ... unsigned integers, ...
        elif base_data_type == DataType.A_UINT32:
            if not isinstance(internal_value, int) or internal_value < 0:
                odxraise(f"Internal value must be a positive integer, not {internal_value!r}")
                internal_value = abs(int(internal_value))

            if base_type_encoding == Encoding.BCD_P:
                # packed BCD
                raw_value = self.__encode_bcd_p(internal_value)
            elif base_type_encoding == Encoding.BCD_UP:
                # unpacked BCD
                raw_value = self.__encode_bcd_up(internal_value)
            elif base_type_encoding in (None, Encoding.NONE):
                # no encoding
                raw_value = internal_value
            else:
                odxraise(f"Illegal encoding ({base_type_encoding}) specified for "
                         f"{base_data_type.value}")

                raw_value = internal_value

            if raw_value.bit_length() > bit_length:
                odxraise(
                    f"The value '{internal_value!r}' cannot be encoded using "
                    f"{bit_length} bits.", EncodeError)
                raw_value &= (1 << bit_length) - 1

        # ... and others (floating point values)
        else:
            odxassert(base_data_type in (DataType.A_FLOAT32, DataType.A_FLOAT64))
            odxassert(base_type_encoding in (None, Encoding.NONE))

            if base_data_type == DataType.A_FLOAT32 and bit_length != 32:
                odxraise(f"Illegal bit length for a float32 object ({bit_length})")
                bit_length = 32
            elif base_data_type == DataType.A_FLOAT64 and bit_length != 64:
                odxraise(f"Illegal bit length for a float64 object ({bit_length})")
                bit_length = 64

            raw_value = float(internal_value)  # type: ignore[arg-type]

        # If the bit length is zero, encode an empty value
        if bit_length == 0:
            self.emplace_bytes(b'')
            return

        format_char = base_data_type.bitstruct_format_letter
        padding = (8 - ((bit_length + self.cursor_bit_position) % 8)) % 8
        odxassert((0 <= padding and padding < 8 and
                   (padding + bit_length + self.cursor_bit_position) % 8 == 0),
                  f"Incorrect padding {padding}")
        left_pad = f"p{padding}" if padding > 0 else ""

        # actually encode the value
        coded = bitstruct.pack(f"{left_pad}{format_char}{bit_length}", raw_value)

        # create the raw mask of used bits for numeric objects
        used_mask_raw = used_mask

        if used_mask_raw is None:
            used_mask_raw = ((1 << bit_length) - 1).to_bytes((bit_length + 7) // 8, "big")

        if self.cursor_bit_position != 0:
            tmp = int.from_bytes(used_mask_raw, "big")
            tmp <<= self.cursor_bit_position
            used_mask_raw = tmp.to_bytes((self.cursor_bit_position + bit_length + 7) // 8, "big")

        # apply byte order to numeric objects
        if not is_highlow_byte_order and base_data_type in [
                DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64
        ]:
            coded = coded[::-1]
            used_mask_raw = used_mask_raw[::-1]

        self.cursor_bit_position = 0
        self.emplace_bytes(coded, obj_used_mask=used_mask_raw)

    def emplace_bytes(self,
                      new_data: bytes,
                      obj_name: str | None = None,
                      obj_used_mask: bytes | None = None) -> None:
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

    @staticmethod
    def __encode_bcd_p(value: int) -> int:
        result = 0
        shift = 0
        while value > 0:
            result |= (value % 10) << shift
            shift += 4
            value //= 10

        return result

    @staticmethod
    def __encode_bcd_up(value: int) -> int:
        result = 0
        shift = 0
        while value > 0:
            result |= (value % 10) << shift
            shift += 8
            value //= 10

        return result
