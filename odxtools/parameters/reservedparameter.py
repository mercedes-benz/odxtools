# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxtypes import DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass(kw_only=True)
class ReservedParameter(Parameter):
    bit_length: int

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "RESERVED"

    @property
    @override
    def is_required(self) -> bool:
        return False

    @property
    @override
    def is_settable(self) -> bool:
        return False

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ReservedParameter":
        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, context))

        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))

        return ReservedParameter(bit_length=bit_length, **kwargs)

    @override
    def get_static_bit_length(self) -> int | None:
        return self.bit_length

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:
        encode_state.cursor_byte_position += (encode_state.cursor_bit_position + self.bit_length +
                                              7) // 8
        encode_state.cursor_bit_position = 0
        encode_state.emplace_bytes(b'', self.short_name)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        return decode_state.extract_atomic_value(
            bit_length=self.bit_length,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            is_highlow_byte_order=False)
