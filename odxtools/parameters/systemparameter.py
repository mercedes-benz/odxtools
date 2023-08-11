# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP


@dataclass
class SystemParameter(ParameterWithDOP):
    sysparam: str

    @property
    def parameter_type(self) -> ParameterType:
        return "SYSTEM"

    def is_required(self):
        raise NotImplementedError("SystemParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError("SystemParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError("Encoding a SystemParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError("Encoding a SystemParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError("Decoding a SystemParameter is not implemented yet.")
