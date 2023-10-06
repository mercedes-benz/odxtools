# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional, Tuple

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise
from .odxtypes import AtomicOdxType, DataType


@dataclass
class StandardLengthType(DiagCodedType):

    bit_length: int
    bit_mask: Optional[int]
    is_condensed_raw: Optional[bool]

    @property
    def dct_type(self) -> DctType:
        return "STANDARD-LENGTH-TYPE"

    def __post_init__(self) -> None:
        if self.bit_mask is not None:
            maskable_types = (DataType.A_UINT32, DataType.A_INT32, DataType.A_BYTEFIELD)
            odxassert(
                self.base_data_type in maskable_types,
                'Can not apply a bit_mask on a value of type {self.base_data_type}',
            )

    def __apply_mask(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if self.bit_mask is None:
            return internal_value
        if self.is_condensed_raw is True:
            raise NotImplementedError("Serialization of condensed bit mask is not supported")
        if isinstance(internal_value, int):
            return internal_value & self.bit_mask
        if isinstance(internal_value, bytes):
            int_value = int.from_bytes(internal_value, 'big')
            int_value = int_value & self.bit_mask
            return int_value.to_bytes(len(internal_value), 'big')

        odxraise(f'Can not apply a bit_mask on a value of type {type(internal_value)}')
        return internal_value

    def get_static_bit_length(self) -> Optional[int]:
        return self.bit_length

    def convert_internal_to_bytes(self, internal_value: AtomicOdxType, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        return self._to_bytes(
            self.__apply_mask(internal_value),
            bit_position,
            self.bit_length,
            self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

    def convert_bytes_to_internal(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[AtomicOdxType, int]:
        internal_value, cursor_position = self._extract_internal(
            decode_state.coded_message,
            decode_state.cursor_position,
            bit_position,
            self.bit_length,
            self.base_data_type,
            self.is_highlow_byte_order,
        )
        internal_value = self.__apply_mask(internal_value)
        return internal_value, cursor_position
