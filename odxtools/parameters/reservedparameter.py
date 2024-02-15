# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional, cast

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..odxtypes import ParameterValue
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
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return (0).to_bytes((self.bit_length + bit_position_int + 7) // 8, "big")

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        # move the cursor
        orig_cursor = decode_state.cursor_byte_position
        if self.byte_position is not None:
            decode_state.cursor_byte_position = decode_state.origin_byte_position + self.byte_position

        decode_state.cursor_byte_position += ((self.bit_position or 0) + self.bit_length + 7) // 8

        decode_state.cursor_byte_position = max(orig_cursor, decode_state.cursor_byte_position)
        decode_state.cursor_bit_position = 0

        # ignore the value of the parameter data
        return cast(int, None)
