# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .parameter import Parameter, ParameterType


@dataclass
class DynamicParameter(Parameter):

    @property
    def parameter_type(self) -> ParameterType:
        return "DYNAMIC"

    def is_required(self):
        raise NotImplementedError("DynamicParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError("DynamicParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError("Encoding a DynamicParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError("Encoding a DynamicParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError("Decoding a DynamicParameter is not implemented yet.")
