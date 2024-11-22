# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from .admindata import AdminData
from .codec import (composite_codec_decode_from_pdu, composite_codec_encode_into_pdu,
                    composite_codec_get_coded_const_prefix, composite_codec_get_free_parameters,
                    composite_codec_get_required_parameters, composite_codec_get_static_bit_length)
from .decodestate import DecodeState
from .element import IdentifiableElement
from .encodestate import EncodeState
from .exceptions import odxraise
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue, ParameterValueDict
from .parameters.createanyparameter import create_any_parameter_from_et
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


class ResponseType(Enum):
    POSITIVE = "POS-RESPONSE"
    NEGATIVE = "NEG-RESPONSE"
    GLOBAL_NEGATIVE = "GLOBAL-NEG-RESPONSE"


@dataclass
class Response(IdentifiableElement):
    """Represents all information related to an UDS response

    This class implements the `CompositeCodec` interface.
    """

    response_type: ResponseType

    admin_data: Optional[AdminData]
    parameters: NamedItemList[Parameter]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Response":
        """Reads a response."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        try:
            response_type = ResponseType(et_element.tag)
        except ValueError:
            response_type = cast(ResponseType, None)
            odxraise(f"Encountered unknown response type '{et_element.tag}'")

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        parameters = NamedItemList([
            create_any_parameter_from_et(et_parameter, doc_frags)
            for et_parameter in et_element.iterfind("PARAMS/PARAM")
        ])
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        return Response(
            response_type=response_type,
            admin_data=admin_data,
            parameters=parameters,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for param in self.parameters:
            result.update(param._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for param in self.parameters:
            param._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.parameters = self.parameters

        try:
            for param in self.parameters:
                param._resolve_snrefs(context)
        finally:
            context.parameters = None

    def encode(self, coded_request: Optional[bytes] = None, **kwargs: ParameterValue) -> bytearray:
        encode_state = EncodeState(triggering_request=coded_request, is_end_of_pdu=True)

        self.encode_into_pdu(physical_value=kwargs, encode_state=encode_state)

        return encode_state.coded_message

    def decode(self, message: bytes) -> ParameterValueDict:
        decode_state = DecodeState(coded_message=message)
        param_values = self.decode_from_pdu(decode_state)

        if not isinstance(param_values, dict):
            odxraise("Decoding a response must result in a dictionary")

        return cast(ParameterValueDict, param_values)

    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        composite_codec_encode_into_pdu(self, physical_value, encode_state)

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        return composite_codec_decode_from_pdu(self, decode_state)

    def get_static_bit_length(self) -> Optional[int]:
        return composite_codec_get_static_bit_length(self)

    @property
    def required_parameters(self) -> List[Parameter]:
        return composite_codec_get_required_parameters(self)

    @property
    def free_parameters(self) -> List[Parameter]:
        return composite_codec_get_free_parameters(self)

    def print_free_parameters_info(self) -> None:
        """Return a human readable description of the structure's
        free parameters.
        """
        from .parameterinfo import parameter_info

        print(parameter_info(self.free_parameters), end="")

    def coded_const_prefix(self, request_prefix: bytes = b'') -> bytes:
        return composite_codec_get_coded_const_prefix(self, request_prefix)
