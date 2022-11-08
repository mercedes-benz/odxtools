# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import List, Iterable, Optional, Union

from .utils import short_name_as_id
from .audience import Audience, read_audience_from_odx
from .functionalclass import FunctionalClass
from .state import State
from .utils import read_description_from_odx
from .exceptions import DecodeError
from .parameters import Parameter
from .odxlink import OdxLinkRef, OdxLinkId, OdxDocFragment, OdxLinkDatabase
from .state_transition import StateTransition
from .structures import Request, Response
from .nameditemlist import NamedItemList
from .message import Message


class DiagService:
    def __init__(self,
                 odx_id: OdxLinkId,
                 short_name: str,
                 request: Union[OdxLinkRef, Request],
                 positive_responses: Union[Iterable[OdxLinkRef], Iterable[Response]],
                 negative_responses: Union[Iterable[OdxLinkRef], Iterable[Response]],
                 long_name: Optional[str] = None,
                 description: Optional[str] = None,
                 semantic: Optional[str] = None,
                 audience: Optional[Audience] = None,
                 functional_class_refs: Iterable[OdxLinkRef] = [],
                 pre_condition_state_refs: Iterable[OdxLinkRef] = [],
                 state_transition_refs: Iterable[OdxLinkRef] = []):
        """Constructs the service.

        Parameters:
        ----------
        odx_id: OdxLinkId
        short_name: str
            the short name of this DIAG-SERVICE
        request: OdxLinkRef | Request
            Reference of a request or a request object
        positive_responses: List[OdxLinkRef] | List[Response]
        negative_responses: List[OdxLinkRef] | List[Response]
        """
        self.odx_id: OdxLinkId = odx_id
        self.short_name: str = short_name
        self.long_name: Optional[str] = long_name
        self.description: Optional[str] = description
        self.semantic: Optional[str] = semantic
        self.audience: Optional[Audience] = audience
        self.functional_class_refs: List[OdxLinkRef] = list(functional_class_refs)
        self._functional_classes: Union[List[FunctionalClass],
                                        NamedItemList[FunctionalClass]] = []
        self.pre_condition_state_refs: List[OdxLinkRef] = list(pre_condition_state_refs)
        self._pre_condition_states: Union[List[State],
                                          NamedItemList[State]] = []
        self.state_transition_refs: List[OdxLinkRef] = list(state_transition_refs)
        self._state_transitions: Union[List[StateTransition],
                                       NamedItemList[StateTransition]] = []

        self._request: Optional[Request]
        self.request_ref: OdxLinkRef
        self._positive_responses: Optional[NamedItemList[Response]]
        self.pos_res_refs: List[OdxLinkRef]
        self._negative_responses: Optional[NamedItemList[Response]]
        self.neg_res_refs: List[OdxLinkRef]

        if isinstance(request, OdxLinkRef):
            self._request = None
            self.request_ref = request
        elif isinstance(request, Request):
            self._request = request
            self.request_ref = OdxLinkRef.from_id(request.odx_id)
        else:
            raise ValueError(
                "request must be a reference to a request or a Request object")

        if all(isinstance(x, Response) for x in positive_responses):
            # TODO (?): Can we tell mypy that positive_responses is definitely of type Iterable[Response]
            self._positive_responses = \
                NamedItemList[Response](short_name_as_id,
                                        positive_responses)  # type: ignore
            self.pos_res_refs = [
                OdxLinkRef.from_id(pr.odx_id) for pr in positive_responses]  # type: ignore
        elif all(isinstance(x, OdxLinkRef) for x in positive_responses):
            self._positive_responses = None
            self.pos_res_refs = positive_responses  # type: ignore
        else:
            raise TypeError(
                "positive_responses must be of type Union[List[OdxLinkRef], List[Response], None]")

        if all(isinstance(x, Response) for x in negative_responses):
            self._negative_responses = \
                NamedItemList[Response](short_name_as_id,
                                        negative_responses)  # type: ignore
            self.neg_res_refs = [
                OdxLinkRef.from_id(nr.odx_id) for nr in negative_responses]  # type: ignore
        elif all(isinstance(x, OdxLinkRef) for x in negative_responses):
            self._negative_responses = None
            self.neg_res_refs = negative_responses  # type: ignore
        else:
            raise TypeError(
                "negative_responses must be of type Union[List[str], List[Response], None]")

    @property
    def request(self) -> Optional[Request]:
        return self._request

    @property
    def free_parameters(self) -> Optional[List[Union[Parameter, "EndOfPduField"]]]: # type: ignore
        """Return the list of parameters which can be freely specified by
        the user when encoding the service's request.
        """
        return self.request.free_parameters if self.request is not None else None

    def print_free_parameters_info(self) -> None:
        """Return a human readable description of the service's
        request's free parameters.
        """
        if self.request is None:
            return

        self.request.print_free_parameters_info()

    @property
    def positive_responses(self) -> Optional[NamedItemList[Response]]:
        return self._positive_responses

    @property
    def negative_responses(self) -> Optional[NamedItemList[Response]]:
        return self._negative_responses

    @property
    def functional_classes(self):
        return self._functional_classes

    @property
    def pre_condition_states(self):
        return self._pre_condition_states

    @property
    def state_transitions(self):
        return self._state_transitions

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self._request = odxlinks.resolve(self.request_ref)
        self._positive_responses = \
            NamedItemList(
                short_name_as_id,
                [odxlinks.resolve(pr_id) for pr_id in self.pos_res_refs])
        self._negative_responses = \
            NamedItemList(
                short_name_as_id,
                [odxlinks.resolve(nr_id) for nr_id in self.neg_res_refs])
        self._functional_classes = \
            NamedItemList(
                short_name_as_id,
                [odxlinks.resolve(fc_id) for fc_id in self.functional_class_refs])
        self._pre_condition_states = \
            NamedItemList(
                short_name_as_id,
                [odxlinks.resolve(st_id) for st_id in self.pre_condition_state_refs])
        self._state_transitions = \
            NamedItemList(
                short_name_as_id,
                [odxlinks.resolve(stt_id) for stt_id in self.state_transition_refs])
        if self.audience:
            self.audience._resolve_references(odxlinks)

    def decode_message(self, message: Union[bytes, bytearray]) -> Message:

        # Check if message is a request or positive or negative response
        interpretable_message_types = []

        if self.request is None or self.positive_responses is None or self.negative_responses is None:
            raise ValueError("References couldn't be resolved or have not been resolved yet."
                             " Try calling `database.resolve_references()`.")

        for message_type in [self.request,
                             *self.positive_responses,
                             *self.negative_responses]:
            prefix = message_type.coded_const_prefix(
                request_prefix=self.request.coded_const_prefix())
            if all(b == message[i] for (i, b) in enumerate(prefix)):
                interpretable_message_types.append(message_type)

        if len(interpretable_message_types) != 1:
            raise DecodeError(
                f"The service {self.short_name} cannot decode the message {message.hex()}")
        message_type = interpretable_message_types[0]
        param_dict = message_type.decode(message)
        return Message(coded_message=message, service=self, structure=message_type, param_dict=param_dict)

    def encode_request(self, **params):
        """
        Composes an UDS request as list of bytes for this service.
        Parameters:
        ----------
        params: dict
            Parameters of the RPC as mapping from SHORT-NAME of the parameter to the physical value
        """
        # make sure that all parameters which are required for
        # encoding are specified (parameters which have a default are
        # optional)
        missing_params = {
            x.short_name
            for x in self.request.required_parameters
        }.difference(params.keys())
        assert not missing_params, f"The parameters {missing_params} are required but missing!"

        # make sure that no unknown parameters are specified
        rq_all_param_names = { x.short_name for x in self.request.parameters }
        assert set(params.keys()).issubset(rq_all_param_names), \
            f"Unknown parameters specified for encoding: {params.keys()}, known parameters are: {rq_all_param_names}"
        return self.request.encode(**params)

    def encode_positive_response(self, coded_request, response_index=0, **params):
        # TODO: Should the user decide the positive response or what are the differences?
        return self.positive_responses[response_index].encode(coded_request, **params)

    def encode_negative_response(self, coded_request, response_index=0, **params):
        return self.negative_responses[response_index].encode(coded_request, **params)

    def __call__(self, **params) -> bytes:
        """Encode a request."""
        return self.encode_request(**params)

    def __str__(self):
        return f"DiagService(odx_id={self.odx_id}, semantic={self.semantic})"

    def __repr__(self):
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.odx_id)

    def __eq__(self, o: object) -> bool:
        return isinstance(o, DiagService) and self.odx_id == o.odx_id


def read_diag_service_from_odx(et_element, doc_frags: List[OdxDocFragment]):

    # logger.info(f"Parsing service based on ET DiagService element: {et_element}")
    short_name = et_element.find("SHORT-NAME").text
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None

    request_ref = OdxLinkRef.from_et(et_element.find("REQUEST-REF"), doc_frags)
    assert request_ref is not None

    pos_res_refs = [ ]
    for el in et_element.iterfind("POS-RESPONSE-REFS/POS-RESPONSE-REF"):
        ref = OdxLinkRef.from_et(el, doc_frags)
        assert ref is not None
        pos_res_refs.append(ref)

    neg_res_refs = []
    for el in et_element.iterfind("NEG-RESPONSE-REFS/NEG-RESPONSE-REF"):
        ref = OdxLinkRef.from_et(el, doc_frags)
        assert ref is not None
        neg_res_refs.append(ref)

    functional_class_refs = []
    for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF"):
         ref = OdxLinkRef.from_et(el, doc_frags)
         assert ref is not None
         functional_class_refs.append(ref)

    pre_condition_state_refs = []
    for el in et_element.iterfind("PRE-CONDITION-STATE-REFS/PRE-CONDITION-STATE-REF"):
        ref = OdxLinkRef.from_et(el, doc_frags)
        assert ref is not None
        pre_condition_state_refs.append(ref)

    state_transition_refs = []
    for el in et_element.iterfind("STATE-TRANSITION-REFS/STATE-TRANSITION-REF"):
        ref = OdxLinkRef.from_et(el, doc_frags)
        assert ref is not None
        state_transition_refs.append(ref)

    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    semantic = et_element.get("SEMANTIC")

    audience = None
    if et_element.find("AUDIENCE"):
        audience = read_audience_from_odx(et_element.find(
            "AUDIENCE"), doc_frags)

    diag_service = DiagService(odx_id,
                               short_name,
                               request_ref,
                               pos_res_refs,
                               neg_res_refs,
                               long_name=long_name,
                               description=description,
                               semantic=semantic,
                               audience=audience,
                               functional_class_refs=functional_class_refs,
                               pre_condition_state_refs=pre_condition_state_refs,
                               state_transition_refs=state_transition_refs)
    return diag_service
