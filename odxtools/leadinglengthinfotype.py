# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import EncodeError, odxassert, odxraise, odxrequire
from .odxlink import OdxDocFragment
from .odxtypes import AtomicOdxType, DataType
from .utils import dataclass_fields_asdict


@dataclass
class LeadingLengthInfoType(DiagCodedType):
    #: bit length of the length specifier field
    #:
    #: this is then followed by the number of bytes specified by that
    #: field, i.e., this is NOT the length of the LeadingLengthInfoType
    #: object.
    bit_length: int

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "LeadingLengthInfoType":
        kwargs = dataclass_fields_asdict(DiagCodedType.from_et(et_element, doc_frags))

        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))

        return LeadingLengthInfoType(bit_length=bit_length, **kwargs)

    def __post_init__(self) -> None:
        odxassert(self.bit_length > 0,
                  "A Leading length info type with bit length == 0 does not make sense.")
        odxassert(
            self.base_data_type in [
                DataType.A_BYTEFIELD,
                DataType.A_ASCIISTRING,
                DataType.A_UNICODE2STRING,
                DataType.A_UTF8STRING,
            ],
            f"A leading length info type cannot have the base data type {self.base_data_type.name}."
        )

    @property
    def dct_type(self) -> DctType:
        return "LEADING-LENGTH-INFO-TYPE"

    @override
    def encode_into_pdu(self, internal_value: AtomicOdxType, encode_state: EncodeState) -> None:

        if not isinstance(internal_value, (str, bytes)):
            odxraise(
                f"LEADING-LENGTH-INFO types can only be used for strings and byte fields, "
                f"not {type(internal_value).__name__}", EncodeError)
            return

        byte_length = self._minimal_byte_length_of(internal_value)

        used_mask = None
        bit_pos = encode_state.cursor_bit_position
        if encode_state.cursor_bit_position != 0 or (bit_pos + self.bit_length) % 8 != 0:
            used_mask = (1 << self.bit_length) - 1
            used_mask <<= bit_pos

        encode_state.emplace_atomic_value(
            internal_value=byte_length,
            used_mask=None,
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        encode_state.emplace_atomic_value(
            internal_value=internal_value,
            used_mask=None,
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:

        # Extract length of the parameter value
        byte_length = decode_state.extract_atomic_value(
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,  # length is an integer
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        if not isinstance(byte_length, int):
            odxraise()

        # Extract actual value
        # TODO: The returned value is None if the byte_length is 0. Maybe change it
        #       to some default value like an empty bytearray() or 0?
        value = decode_state.extract_atomic_value(
            bit_length=8 * byte_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

        return value
