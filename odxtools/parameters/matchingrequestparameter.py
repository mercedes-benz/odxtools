# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import EncodeError, odxraise, odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxtypes import DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass(kw_only=True)
class MatchingRequestParameter(Parameter):
    request_byte_position: int
    byte_length: int

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "MATCHING-REQUEST-PARAM"

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
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "MatchingRequestParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, context))

        request_byte_position = int(odxrequire(et_element.findtext("REQUEST-BYTE-POS")))
        byte_length = int(odxrequire(et_element.findtext("BYTE-LENGTH")))

        return MatchingRequestParameter(
            request_byte_position=request_byte_position, byte_length=byte_length, **kwargs)

    @override
    def get_static_bit_length(self) -> int | None:
        return 8 * self.byte_length

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:
        if encode_state.triggering_request is None:
            odxraise(
                f"Parameter '{self.short_name}' is of matching request type,"
                f" but no original request has been specified.", EncodeError)
            return

        rq_pos = self.request_byte_position
        rq_len = self.byte_length

        if len(encode_state.triggering_request) < rq_pos + rq_len:
            odxraise(
                f"Specified triggering request 0x{encode_state.triggering_request.hex()} "
                f"is not long enough to encode matching request parameter "
                f"'{self.short_name}': Have {len(encode_state.triggering_request)} "
                f"bytes, need at least {rq_pos + rq_len} bytes", EncodeError)
            return

        encode_state.emplace_bytes(encode_state.triggering_request[rq_pos:rq_pos + rq_len],
                                   self.short_name)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        return decode_state.extract_atomic_value(
            bit_length=self.byte_length * 8,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            is_highlow_byte_order=False)
