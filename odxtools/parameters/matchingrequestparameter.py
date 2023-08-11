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
