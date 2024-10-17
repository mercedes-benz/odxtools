# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast
from xml.etree import ElementTree

from .comparaminstance import ComparamInstance
from .diagcomm import DiagComm
from .exceptions import DecodeError, DecodeMismatch, odxassert, odxraise, odxrequire
from .message import Message
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue, odxstr_to_bool
from .parameters.parameter import Parameter
from .request import Request
from .response import Response
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


class Addressing(Enum):
    FUNCTIONAL = "FUNCTIONAL"
    PHYSICAL = "PHYSICAL"
    FUNCTIONAL_OR_PHYSICAL = "FUNCTIONAL-OR-PHYSICAL"


class TransMode(Enum):
    SEND_ONLY = "SEND-ONLY"
    RECEIVE_ONLY = "RECEIVE-ONLY"
    SEND_AND_RECEIVE = "SEND-AND-RECEIVE"
    SEND_OR_RECEIVE = "SEND-OR-RECEIVE"


@dataclass
class DiagService(DiagComm):
    """Representation of a diagnostic service description.
    """

    comparam_refs: List[ComparamInstance]

    request_ref: OdxLinkRef
    pos_response_refs: List[OdxLinkRef]
    neg_response_refs: List[OdxLinkRef]

    # note that the spec has a typo here: it calls the corresponding
    # XML tag POS-RESPONSE-SUPPRESSABLE...
    # TODO: pos_response_suppressible: Optional[PosResponseSuppressible]

    is_cyclic_raw: Optional[bool]
    is_multiple_raw: Optional[bool]
    addressing_raw: Optional[Addressing]
    transmission_mode_raw: Optional[TransMode]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagService":

        kwargs = dataclass_fields_asdict(DiagComm.from_et(et_element, doc_frags))

        comparam_refs = [
            ComparamInstance.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPARAM-REFS/COMPARAM-REF")
        ]

        request_ref = odxrequire(OdxLinkRef.from_et(et_element.find("REQUEST-REF"), doc_frags))

        pos_response_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("POS-RESPONSE-REFS/POS-RESPONSE-REF")
        ]

        neg_response_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("NEG-RESPONSE-REFS/NEG-RESPONSE-REF")
        ]

        # TODO: POS-RESPONSE-SUPPRESSABLE

        is_cyclic_raw = odxstr_to_bool(et_element.get("IS-CYCLIC"))
        is_multiple_raw = odxstr_to_bool(et_element.get("IS-MULTIPLE"))

        addressing_raw: Optional[Addressing] = None
        if (addressing_raw_str := et_element.get("ADDRESSING")) is not None:
            try:
                addressing_raw = Addressing(addressing_raw_str)
            except ValueError:
                addressing_raw = cast(Addressing, None)
                odxraise(f"Encountered unknown addressing type '{addressing_raw_str}'")

        transmission_mode_raw: Optional[TransMode] = None
        if (transmission_mode_raw_str := et_element.get("TRANSMISSION-MODE")) is not None:
            try:
                transmission_mode_raw = TransMode(transmission_mode_raw_str)
            except ValueError:
                transmission_mode_raw = cast(TransMode, None)
                odxraise(f"Encountered unknown transmission mode '{transmission_mode_raw_str}'")

        return DiagService(
            comparam_refs=comparam_refs,
            request_ref=request_ref,
            pos_response_refs=pos_response_refs,
            neg_response_refs=neg_response_refs,
            is_cyclic_raw=is_cyclic_raw,
            is_multiple_raw=is_multiple_raw,
            addressing_raw=addressing_raw,
            transmission_mode_raw=transmission_mode_raw,
            **kwargs)

    @property
    def request(self) -> Optional[Request]:
        return self._request

    @property
    def free_parameters(self) -> List[Parameter]:
        """Return the list of parameters which can be freely specified by
        the user when encoding the service's request.
        """
        return self.request.free_parameters if self.request is not None else []

    def print_free_parameters_info(self) -> None:
        """Return a human readable description of the service's
        request's free parameters.
        """
        if self.request is None:
            return

        self.request.print_free_parameters_info()

    @property
    def positive_responses(self) -> NamedItemList[Response]:
        return self._positive_responses

    @property
    def negative_responses(self) -> NamedItemList[Response]:
        return self._negative_responses

    @property
    def comparams(self) -> NamedItemList[ComparamInstance]:
        return self._comparams

    @property
    def addressing(self) -> Addressing:
        return self.addressing_raw or Addressing.PHYSICAL

    @property
    def transmission_mode(self) -> TransMode:
        return self.transmission_mode_raw or TransMode.SEND_AND_RECEIVE

    @property
    def is_cyclic(self) -> bool:
        return self.is_cyclic_raw is True

    @property
    def is_multiple(self) -> bool:
        return self.is_multiple_raw is True

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for cpr in self.comparam_refs:
            result.update(cpr._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for cpr in self.comparam_refs:
            cpr._resolve_odxlinks(odxlinks)

        self._request = odxlinks.resolve(self.request_ref, Request)

        self._positive_responses = NamedItemList[Response](
            [odxlinks.resolve(x, Response) for x in self.pos_response_refs])

        self._negative_responses = NamedItemList[Response](
            [odxlinks.resolve(x, Response) for x in self.neg_response_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.diag_service = self

        super()._resolve_snrefs(context)

        for cpr in self.comparam_refs:
            cpr._resolve_snrefs(context)

        # The named item list of communication parameters is created
        # here because ComparamInstance.short_name is only valid after
        # reference resolution
        self._comparams = NamedItemList(self.comparam_refs)

        context.diag_service = None

    def decode_message(self, raw_message: bytes) -> Message:
        request_prefix = b''
        candidate_coding_objects: List[Union[Request, Response]] = [
            *self.positive_responses, *self.negative_responses
        ]
        if self.request is not None:
            request_prefix = self.request.coded_const_prefix()
            candidate_coding_objects.append(self.request)

        coding_objects: List[Union[Request, Response]] = []
        for candidate_coding_object in candidate_coding_objects:
            prefix = candidate_coding_object.coded_const_prefix(request_prefix=request_prefix)
            if len(raw_message) >= len(prefix) and prefix == raw_message[:len(prefix)]:
                coding_objects.append(candidate_coding_object)

        result_list: List[Message] = []
        for coding_object in coding_objects:
            try:
                result_list.append(
                    Message(
                        coded_message=raw_message,
                        service=self,
                        coding_object=coding_object,
                        param_dict=coding_object.decode(raw_message)))
            except DecodeMismatch:
                # An NRC-CONST or environment data parameter
                # encountered a non-matching value -> coding object
                # does not apply
                pass

        if len(result_list) < 1:
            odxraise(f"The service {self.short_name} cannot decode the message {raw_message.hex()}",
                     DecodeError)
            return Message(
                coded_message=raw_message, service=self, coding_object=None, param_dict={})
        elif len(result_list) > 1:
            odxraise(
                f"The service {self.short_name} cannot uniquely decode the message {raw_message.hex()}",
                DecodeError)

        return result_list[0]

    def encode_request(self, **kwargs: ParameterValue) -> bytes:
        """Prepare an array of bytes ready to be send over the wire
        for the request of this service.
        """
        # make sure that all parameters which are required for
        # encoding are specified (parameters which have a default are
        # optional)
        if self.request is None:
            return b''

        missing_params = {x.short_name
                          for x in self.request.required_parameters}.difference(kwargs.keys())
        odxassert(
            len(missing_params) == 0, f"The parameters {missing_params} are required but missing!")

        # make sure that no unknown parameters are specified
        rq_all_param_names = {x.short_name for x in self.request.parameters}
        odxassert(
            set(kwargs.keys()).issubset(rq_all_param_names),
            f"Unknown parameters specified for encoding: {kwargs.keys()}, "
            f"known parameters are: {rq_all_param_names}")
        return self.request.encode(**kwargs)

    def encode_positive_response(self,
                                 coded_request: bytes,
                                 response_index: int = 0,
                                 **kwargs: ParameterValue) -> bytes:
        # TODO: Should the user decide the positive response or what are the differences?
        return self.positive_responses[response_index].encode(coded_request, **kwargs)

    def encode_negative_response(self,
                                 coded_request: bytes,
                                 response_index: int = 0,
                                 **kwargs: ParameterValue) -> bytes:
        return self.negative_responses[response_index].encode(coded_request, **kwargs)

    def __call__(self, **kwargs: ParameterValue) -> bytes:
        """Encode a request."""
        return self.encode_request(**kwargs)
