# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from ..decodestate import DecodeState
from ..exceptions import DecodeError

from .parameterbase import Parameter


class ReservedParameter(Parameter):
    def __init__(self,
                 short_name,
                 bit_length,
                 **kwargs):
        super().__init__(short_name,
                         parameter_type="RESERVED",
                         **kwargs)
        self._bit_length = bit_length

    @property
    def bit_length(self):
        return self._bit_length

    def is_required(self):
        return False

    def is_optional(self):
        return False

    def get_coded_value(self):
        return 0

    def get_coded_value_as_bytes(self, encode_state):
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return int(0).to_bytes((self.bit_length + bit_position_int + 7) // 8, "big")

    def decode_from_pdu(self, decode_state: DecodeState):
        byte_position = self.byte_position if self.byte_position is not None else decode_state.next_byte_position
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        byte_length = (self.bit_length + bit_position_int + 7) // 8
        val_as_bytes = decode_state.coded_message[byte_position:byte_position+byte_length]
        next_byte_position = byte_position + byte_length

        # Check that reserved bits are 0
        expected = sum(2**i for i in range(bit_position_int,
                                           bit_position_int + self.bit_length))
        actual = int.from_bytes(val_as_bytes, "big")

        # Bit-wise compare if reserved bits are 0.
        if expected & actual != 0:
            raise DecodeError(
                f"Reserved bits must be Zero! "
                f"The parameter {self.short_name} expected {self.bit_length} bits to be Zero starting at bit position {bit_position_int} "
                f"at byte position {byte_position} "
                f"in coded message {decode_state.coded_message.hex()}."
            )

        return None, next_byte_position

    def __repr__(self):
        repr_str = f"ReservedParameter(short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.bit_length is not None:
            repr_str += f", bit_length='{self.bit_length}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"
