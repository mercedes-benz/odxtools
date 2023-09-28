# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Tuple

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..odxlink import OdxLinkRef
from ..odxtypes import ParameterValue
from .parameter import Parameter, ParameterType


@dataclass
class TableEntryParameter(Parameter):
    target: str
    table_row_ref: OdxLinkRef

    @property
    def parameter_type(self) -> ParameterType:
        return "TABLE-ENTRY"

    @property
    def is_required(self) -> bool:
        raise NotImplementedError("TableKeyParameter.is_required is not implemented yet.")

    @property
    def is_settable(self) -> bool:
        raise NotImplementedError("TableKeyParameter.is_settable is not implemented yet.")

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        raise NotImplementedError("Encoding a TableKeyParameter is not implemented yet.")

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[ParameterValue, int]:
        raise NotImplementedError("Decoding a TableKeyParameter is not implemented yet.")
