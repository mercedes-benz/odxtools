# SPDX-License-Identifier: MIT
import typing
from typing import runtime_checkable

from .decodestate import DecodeState
from .encodestate import EncodeState
from .odxtypes import ParameterValue


@runtime_checkable
class Codec(typing.Protocol):
    """Any object which can be en- or decoded to be transferred over
    the wire implements this API.
    """

    @property
    def short_name(self) -> str:
        return ""

    def encode_into_pdu(self, physical_value: ParameterValue | None,
                        encode_state: EncodeState) -> None:
        ...

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        ...

    def get_static_bit_length(self) -> int | None:
        ...
