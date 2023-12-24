# SPDX-License-Identifier: MIT
import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Tuple, Union

try:
    import bitstruct.c as bitstruct
except ImportError:
    import bitstruct

from . import exceptions
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise
from .odxlink import OdxLinkDatabase, OdxLinkId
from .odxtypes import AtomicOdxType, DataType

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

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

# Allowed diag-coded types
DctType = Literal[
    "LEADING-LENGTH-INFO-TYPE",
    "MIN-MAX-LENGTH-TYPE",
    "PARAM-LENGTH-INFO-TYPE",
    "STANDARD-LENGTH-TYPE",
]


@dataclass
class DiagCodedType(abc.ABC):

    base_data_type: DataType
    base_type_encoding: Optional[str]
    is_highlow_byte_order_raw: Optional[bool]

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:  # noqa: B027
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:  # noqa: B027
        """Recursively resolve any odxlinks references"""
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:  # noqa: B027
        """Recursively resolve any short-name references"""
        pass

    def get_static_bit_length(self) -> Optional[int]:
        return None

    @property
    @abc.abstractmethod
    def dct_type(self) -> DctType:
        pass

    @property
    def is_highlow_byte_order(self) -> bool:
        return self.is_highlow_byte_order_raw in [None, True]

    @staticmethod
    def _extract_internal_value(
        coded_message: bytes,
        byte_position: int,
        bit_position: int,
        bit_length: int,
        base_data_type: DataType,
        is_highlow_byte_order: bool,
    ) -> Tuple[AtomicOdxType, int]:
        """Extract an internal value from a blob of raw bytes.

        :return: Tuple with the internal value of the object and the
                 byte position of the first undecoded byte after the
                 extracted object.
        """
        # If the bit length is zero, return "empty" values of each type
        if bit_length == 0:
            return base_data_type.as_python_type()(), byte_position

        byte_length = (bit_length + bit_position + 7) // 8
        if byte_position + byte_length > len(coded_message):
            raise DecodeError(f"Expected a longer message.")
        cursor_position = byte_position + byte_length
        extracted_bytes = coded_message[byte_position:cursor_position]

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

        padding = (8 - (bit_length + bit_position) % 8) % 8
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

        return internal_value, cursor_position

    @staticmethod
    def _encode_internal_value(
        internal_value: AtomicOdxType,
        bit_position: int,
        bit_length: int,
        base_data_type: DataType,
        is_highlow_byte_order: bool,
    ) -> bytes:
        """Convert the internal_value to bytes."""
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
            if (base_data_type in [
                    DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64
            ] and base_data_type != 0):
                raise EncodeError(
                    f"The number {repr(internal_value)} cannot be encoded into {bit_length} bits.")
            return b''

        char = ODX_TYPE_TO_FORMAT_LETTER[base_data_type]
        padding = (8 - ((bit_length + bit_position) % 8)) % 8
        odxassert((0 <= padding and padding < 8 and (padding + bit_length + bit_position) % 8 == 0),
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

        return coded

    def _minimal_byte_length_of(self, internal_value: Union[bytes, str]) -> int:
        """Helper method to get the minimal byte length.
        (needed for LeadingLength- and MinMaxLengthType)
        """
        # A_BYTEFIELD, A_ASCIISTRING, A_UNICODE2STRING, A_UTF8STRING
        if self.base_data_type == DataType.A_BYTEFIELD:
            byte_length = len(internal_value)
        elif self.base_data_type in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING]:
            if not isinstance(internal_value, str):
                odxraise()

            # TODO: Handle different encodings
            byte_length = len(bytes(internal_value, "utf-8"))
        elif self.base_data_type == DataType.A_UNICODE2STRING:
            if not isinstance(internal_value, str):
                odxraise()

            byte_length = len(bytes(internal_value, "utf-16-le"))
            odxassert(
                byte_length % 2 == 0, f"The bit length of A_UNICODE2STRING must"
                f" be a multiple of 16 but is {8*byte_length}")
        return byte_length

    @abc.abstractmethod
    def convert_internal_to_bytes(self, internal_value: AtomicOdxType, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        """Encode the internal value.

        Parameters
        ----------
        internal_value : python type corresponding to self.base_data_type
            the value to be encoded
        bit_position : int

        length_keys : Dict[OdxLinkId, int]
            mapping from ID (of the length key) to bit length
            (only needed for ParamLengthInfoType)
        """
        pass

    @abc.abstractmethod
    def convert_bytes_to_internal(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[AtomicOdxType, int]:
        """Decode the parameter value from the coded message.

        Parameters
        ----------
        decode_state : DecodeState
            The decoding state

        Returns
        -------
        str or int or bytes or dict
            the decoded parameter value
        int
            the next byte position after the extracted parameter
        """
        pass
