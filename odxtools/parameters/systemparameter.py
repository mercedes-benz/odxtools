# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Tuple

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..odxtypes import ParameterValue
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP


@dataclass
class SystemParameter(ParameterWithDOP):
    sysparam: str

    @property
    def parameter_type(self) -> ParameterType:
        return "SYSTEM"

    @property
    def is_required(self) -> bool:
        raise NotImplementedError("SystemParameter.is_required is not implemented yet.")

    @property
    def is_settable(self) -> bool:
        raise NotImplementedError("SystemParameter.is_settable is not implemented yet.")

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        raise NotImplementedError("Encoding a SystemParameter is not implemented yet.")

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[ParameterValue, int]:
        raise NotImplementedError("Decoding a SystemParameter is not implemented yet.")
