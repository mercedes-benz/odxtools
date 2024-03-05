# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..odxtypes import DataType, ParameterValue
from .parameter import Parameter, ParameterType


@dataclass
class ReservedParameter(Parameter):
    bit_length: int

    @property
    def parameter_type(self) -> ParameterType:
        return "RESERVED"

    @property
    def is_required(self) -> bool:
        return False

    @property
    def is_settable(self) -> bool:
        return False

    def get_static_bit_length(self) -> Optional[int]:
        return self.bit_length

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        return (0).to_bytes(((self.bit_position or 0) + self.bit_length + 7) // 8, "big")

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        decode_state.cursor_byte_position += ((self.bit_position or 0) + self.bit_length + 7) // 8

        return decode_state.extract_atomic_value(
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,
            is_highlow_byte_order=False)
