# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, cast
from xml.etree import ElementTree

from .admindata import AdminData
from .compositecodec import (composite_codec_decode_from_pdu, composite_codec_encode_into_pdu,
                             composite_codec_get_coded_const_prefix,
                             composite_codec_get_free_parameters,
                             composite_codec_get_required_parameters,
                             composite_codec_get_static_bit_length)
from .decodestate import DecodeState
from .element import IdentifiableElement
from .encodestate import EncodeState
from .exceptions import odxraise
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue, ParameterValueDict
from .parameters.createanyparameter import create_any_parameter_from_et
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class Request(IdentifiableElement):
    """Represents all information related to an UDS request

    This class implements the `CompositeCodec` interface.
    """
    admin_data: AdminData | None = None
    parameters: NamedItemList[Parameter] = field(default_factory=NamedItemList)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @property
    def required_parameters(self) -> list[Parameter]:
        return composite_codec_get_required_parameters(self)

    @property
    def free_parameters(self) -> list[Parameter]:
        return composite_codec_get_free_parameters(self)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Request":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        parameters = NamedItemList([
            create_any_parameter_from_et(et_parameter, context)
            for et_parameter in et_element.iterfind("PARAMS/PARAM")
        ])
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return Request(admin_data=admin_data, parameters=parameters, sdgs=sdgs, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        for param in self.parameters:
            result.update(param._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        for param in self.parameters:
            param._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.request = self
        context.parameters = self.parameters

        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)

        for param in self.parameters:
            param._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

        context.request = None
        context.parameters = None

    def get_static_bit_length(self) -> int | None:
        return composite_codec_get_static_bit_length(self)

    def print_free_parameters_info(self) -> None:
        """Print a human readable description of the composite codec's
        free parameters to `stdout`
        """
        from .parameterinfo import parameter_info

        print(parameter_info(self.free_parameters), end="")

    def encode(self, **kwargs: ParameterValue) -> bytearray:
        encode_state = EncodeState(is_end_of_pdu=True)

        self.encode_into_pdu(physical_value=kwargs, encode_state=encode_state)

        return encode_state.coded_message

    def decode(self, message: bytes | bytearray) -> ParameterValueDict:
        decode_state = DecodeState(coded_message=bytes(message))
        param_values = self.decode_from_pdu(decode_state)

        if not isinstance(param_values, dict):
            odxraise("Decoding a request must result in a dictionary")

        return cast(ParameterValueDict, param_values)

    def encode_into_pdu(self, physical_value: ParameterValue | None,
                        encode_state: EncodeState) -> None:
        composite_codec_encode_into_pdu(self, physical_value, encode_state)

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        return composite_codec_decode_from_pdu(self, decode_state)

    def coded_const_prefix(self, request_prefix: bytes = b'') -> bytearray:
        return composite_codec_get_coded_const_prefix(self, request_prefix)
