# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .encoding import Encoding, get_string_encoding
from .exceptions import DecodeError, odxassert, odxraise, strict_mode
from .odxtypes import AtomicOdxType, DataType, ParameterValue

try:
    import bitstruct.c as bitstruct
except ImportError:
    import bitstruct

if TYPE_CHECKING:
    from .parameters.parameter import Parameter
    from .tablerow import TableRow


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
    length_keys: dict[str, int] = field(default_factory=dict)

    #: values of the table key parameters decoded so far
    table_keys: dict[str, "TableRow"] = field(default_factory=dict)

    #: List of parameters that have been decoded so far. The journal
    #: is used by some types of parameters which depend on the values of
    #: other parameters; i.e., environment data description parameters
    journal: list[tuple["Parameter", ParameterValue | None]] = field(default_factory=list)

    def extract_atomic_value(
        self,
        *,
        bit_length: int,
        base_data_type: DataType,
        base_type_encoding: Encoding | None,
        is_highlow_byte_order: bool,
    ) -> AtomicOdxType:
        """Extract an internal value from a blob of raw bytes.

        :return: Tuple with the internal value of the object and the
                 byte position of the first undecoded byte after the
                 extracted object.
        """
        # If the bit length is zero, return "empty" values of each type
        if bit_length == 0:
            return base_data_type.python_type()

        if base_data_type == DataType.A_FLOAT32 and bit_length != 32:
            odxraise("The bit length of FLOAT32 values must be 32 bits")
            bit_length = 32
        elif base_data_type == DataType.A_FLOAT64 and bit_length != 64:
            odxraise("The bit length of FLOAT64 values must be 64 bits")
            bit_length = 64

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
        raw_value, = bitstruct.unpack_from(
            f"{base_data_type.bitstruct_format_letter}{bit_length}",
            extracted_bytes,
            offset=padding)
        internal_value: AtomicOdxType

        # Deal with raw byte fields, ...
        if base_data_type == DataType.A_BYTEFIELD:
            odxassert(
                base_type_encoding in (None, Encoding.NONE, Encoding.BCD_P, Encoding.BCD_UP),
                f"Illegal encoding '{base_type_encoding}' for A_BYTEFIELD")

            # note that we do not ensure that BCD-encoded byte fields
            # only represent "legal" values
            internal_value = raw_value

        # ... string types, ...
        elif base_data_type in (DataType.A_UTF8STRING, DataType.A_ASCIISTRING,
                                DataType.A_UNICODE2STRING):
            text_errors = 'strict' if strict_mode else 'replace'
            str_encoding = get_string_encoding(base_data_type, base_type_encoding,
                                               is_highlow_byte_order)
            if str_encoding is not None:
                internal_value = raw_value.decode(str_encoding, errors=text_errors)
            else:
                internal_value = "ERROR"

        # ... signed integers, ...
        elif base_data_type == DataType.A_INT32:
            if base_type_encoding == Encoding.ONEC:
                # one-complement
                sign_bit = 1 << (bit_length - 1)
                if raw_value < sign_bit:
                    internal_value = raw_value
                else:
                    # python defines the bitwise inversion of a
                    # positive integer value x as ~x = -(x + 1).
                    internal_value = -((1 << bit_length) - raw_value - 1)
            elif base_type_encoding in (None, Encoding.TWOC):
                # two-complement
                sign_bit = 1 << (bit_length - 1)
                if raw_value < sign_bit:
                    internal_value = raw_value
                else:
                    internal_value = -((1 << bit_length) - raw_value)
            elif base_type_encoding == Encoding.SM:
                # sign-magnitude
                sign_bit = 1 << (bit_length - 1)
                if raw_value < sign_bit:
                    internal_value = raw_value
                else:
                    internal_value = -(raw_value - sign_bit)
            else:
                odxraise(f"Illegal encoding ({base_type_encoding}) specified for "
                         f"{base_data_type.value}")

                if base_type_encoding == Encoding.BCD_P:
                    internal_value = self.__decode_bcd_p(raw_value)
                elif base_type_encoding == Encoding.BCD_UP:
                    internal_value = self.__decode_bcd_up(raw_value)
                else:
                    internal_value = raw_value

        # ... unsigned integers, ...
        elif base_data_type == DataType.A_UINT32:
            if base_type_encoding == Encoding.BCD_P:
                internal_value = self.__decode_bcd_p(raw_value)
            elif base_type_encoding == Encoding.BCD_UP:
                internal_value = self.__decode_bcd_up(raw_value)
            elif base_type_encoding in (None, Encoding.NONE):
                # no encoding
                internal_value = raw_value
            else:
                odxraise(f"Illegal encoding ({base_type_encoding}) specified for "
                         f"{base_data_type.value}")

                internal_value = raw_value

        # ... and others (floating point values)
        else:
            odxassert(base_data_type in (DataType.A_FLOAT32, DataType.A_FLOAT64))
            odxassert(
                base_type_encoding in (None, Encoding.NONE),
                f"Specified illegal encoding '{base_type_encoding}' for float object")

            internal_value = float(raw_value)

        self.cursor_byte_position += byte_length
        self.cursor_bit_position = 0

        return internal_value

    @staticmethod
    def __decode_bcd_p(value: int) -> int:
        # packed BCD
        result = 0
        factor = 1
        while value > 0:
            result += (value & 0xf) * factor
            factor *= 10
            value >>= 4

        return result

    @staticmethod
    def __decode_bcd_up(value: int) -> int:
        # unpacked BCD
        result = 0
        factor = 1
        while value > 0:
            result += (value & 0xf) * factor
            factor *= 10
            value >>= 8

        return result
