# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import EncodeError
from .parameter import Parameter, ParameterType


@dataclass
class MatchingRequestParameter(Parameter):
    request_byte_position: int
    byte_length: int

    @property
    def parameter_type(self) -> ParameterType:
        return "MATCHING-REQUEST-PARAM"

    @property
    def bit_length(self):
        return 8 * self.byte_length

    def is_required(self):
        return True

    def is_optional(self):
        return False

    def get_coded_value(self, request_value=None):
        return request_value

    def get_coded_value_as_bytes(self, encode_state: EncodeState):
        if not encode_state.triggering_request:
            raise EncodeError(f"Parameter '{self.short_name}' is of matching request type,"
                              " but no original request has been specified.")
        return encode_state.triggering_request[self
                                               .request_byte_position:self.request_byte_position +
                                               self.byte_length]

    def decode_from_pdu(self, decode_state: DecodeState):
        byte_position = (
            self.byte_position
            if self.byte_position is not None else decode_state.next_byte_position)
        bit_position = self.bit_position if self.bit_position is not None else 0
        byte_length = (self.bit_length + bit_position + 7) // 8
        val_as_bytes = decode_state.coded_message[byte_position:byte_position + byte_length]

        return val_as_bytes, byte_position + byte_length

    def __repr__(self):
        repr_str = f"MatchingRequestParameter(short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.request_byte_position is not None:
            repr_str += f", request_byte_position='{self.request_byte_position}'"
        if self.byte_length is not None:
            repr_str += f", byte_length='{self.byte_length}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"

    def __str__(self):
        return (
            super().__str__() +
            f"\n Request byte position = {self.request_byte_position}, byte length = {self.byte_length}"
        )
