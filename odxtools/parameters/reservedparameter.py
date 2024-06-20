# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass
class ReservedParameter(Parameter):
    bit_length: int

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ReservedParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))

        return ReservedParameter(bit_length=bit_length, **kwargs)

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

    @override
    def get_static_bit_length(self) -> Optional[int]:
        return self.bit_length

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
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
            is_highlow_byte_order=False)
