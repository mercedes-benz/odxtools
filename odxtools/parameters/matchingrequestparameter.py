# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import EncodeError, odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass
class MatchingRequestParameter(Parameter):
    request_byte_position: int
    byte_length: int

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MatchingRequestParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        request_byte_position = int(odxrequire(et_element.findtext("REQUEST-BYTE-POS")))
        byte_length = int(odxrequire(et_element.findtext("BYTE-LENGTH")))

        return MatchingRequestParameter(
            request_byte_position=request_byte_position, byte_length=byte_length, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "MATCHING-REQUEST-PARAM"

    @override
    def get_static_bit_length(self) -> Optional[int]:
        return 8 * self.byte_length

    @property
    @override
    def is_required(self) -> bool:
        return False

    @property
    @override
    def is_settable(self) -> bool:
        return False

    @override
    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        if not encode_state.triggering_request:
            raise EncodeError(f"Parameter '{self.short_name}' is of matching request type,"
                              " but no original request has been specified.")
        return encode_state.triggering_request[self
                                               .request_byte_position:self.request_byte_position +
                                               self.byte_length]

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        result = decode_state.extract_atomic_value(
            bit_length=self.byte_length * 8,
            base_data_type=DataType.A_UINT32,
            is_highlow_byte_order=False)

        return result
