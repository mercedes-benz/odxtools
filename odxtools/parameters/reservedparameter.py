# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass

from ..decodestate import DecodeState
from ..exceptions import DecodeError
from .parameter import Parameter, ParameterType


@dataclass
class ReservedParameter(Parameter):
    bit_length_raw: int

    @property
    def parameter_type(self) -> ParameterType:
        return "RESERVED"

    def is_required(self):
        return False

    def is_optional(self):
        return False

    @property
    def bit_length(self) -> int:
        # this is a bit hacky: the parent class already specifies
        # bit_length as a function property, and we need to change
        # this to return the value from the XML here. Since function
        # attributes cannot be overridden by non-function ones, we
        # need to take the "bit_length_raw" detour...
        return self.bit_length_raw

    def get_coded_value(self):
        return 0

    def get_coded_value_as_bytes(self, encode_state):
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return int(0).to_bytes((self.bit_length + bit_position_int + 7) // 8, "big")

    def decode_from_pdu(self, decode_state: DecodeState):
        byte_position = (
            self.byte_position
            if self.byte_position is not None else decode_state.next_byte_position)
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        byte_length = (self.bit_length_raw + bit_position_int + 7) // 8
        val_as_bytes = decode_state.coded_message[byte_position:byte_position + byte_length]
        next_byte_position = byte_position + byte_length

        # Check that reserved bits are 0
        expected = sum(
            2**i for i in range(bit_position_int, bit_position_int + self.bit_length_raw))
        actual = int.from_bytes(val_as_bytes, "big")

        # Bit-wise compare if reserved bits are 0.
        if expected & actual != 0:
            warnings.warn(
                f"Reserved bits must be Zero! "
                f"The parameter {self.short_name} expected {self.bit_length} bits to be Zero starting at bit position {bit_position_int} "
                f"at byte position {byte_position} "
                f"in coded message {decode_state.coded_message.hex()}.",
                DecodeError,
            )

        return None, next_byte_position
