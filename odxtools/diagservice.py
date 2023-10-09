# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .exceptions import DecodeError, odxassert, odxrequire
from .functionalclass import FunctionalClass
from .message import Message
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue
from .parameters.parameter import Parameter
from .request import Request
from .response import Response
from .specialdatagroup import SpecialDataGroup
from .state import State
from .statetransition import StateTransition
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DiagService(IdentifiableElement):
    """Representation of a diagnostic service description.
    """

    request_ref: OdxLinkRef
    pos_response_refs: List[OdxLinkRef]
    neg_response_refs: List[OdxLinkRef]
    admin_data: Optional[AdminData]
    semantic: Optional[str]
    audience: Optional[Audience]
    functional_class_refs: Iterable[OdxLinkRef]
    pre_condition_state_refs: Iterable[OdxLinkRef]
    state_transition_refs: Iterable[OdxLinkRef]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagService":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        request_ref = odxrequire(OdxLinkRef.from_et(et_element.find("REQUEST-REF"), doc_frags))

        pos_response_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("POS-RESPONSE-REFS/POS-RESPONSE-REF")
        ]

        neg_response_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("NEG-RESPONSE-REFS/NEG-RESPONSE-REF")
        ]

        functional_class_refs = []
        for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF"):
            ref = odxrequire(OdxLinkRef.from_et(el, doc_frags))
            functional_class_refs.append(ref)

        pre_condition_state_refs = []
        for el in et_element.iterfind("PRE-CONDITION-STATE-REFS/PRE-CONDITION-STATE-REF"):
            ref = odxrequire(OdxLinkRef.from_et(el, doc_frags))
            pre_condition_state_refs.append(ref)

        state_transition_refs = []
        for el in et_element.iterfind("STATE-TRANSITION-REFS/STATE-TRANSITION-REF"):
            ref = odxrequire(OdxLinkRef.from_et(el, doc_frags))
            state_transition_refs.append(ref)

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        semantic = et_element.get("SEMANTIC")

        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, doc_frags)

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return DiagService(
            request_ref=request_ref,
            pos_response_refs=pos_response_refs,
            neg_response_refs=neg_response_refs,
            admin_data=admin_data,
            semantic=semantic,
            audience=audience,
            functional_class_refs=functional_class_refs,
            pre_condition_state_refs=pre_condition_state_refs,
            state_transition_refs=state_transition_refs,
            sdgs=sdgs,
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
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        return self._functional_classes

    @property
    def pre_condition_states(self) -> NamedItemList[State]:
        return self._pre_condition_states

    @property
    def state_transitions(self) -> NamedItemList[StateTransition]:
        return self._state_transitions

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._request = odxlinks.resolve(self.request_ref)

        self._positive_responses = NamedItemList[Response](
            [odxlinks.resolve(x, Response) for x in self.pos_response_refs])

        self._negative_responses = NamedItemList[Response](
            [odxlinks.resolve(x, Response) for x in self.neg_response_refs])

        self._functional_classes = NamedItemList(
            [odxlinks.resolve(fc_ref, FunctionalClass) for fc_ref in self.functional_class_refs])
        self._pre_condition_states = NamedItemList(
            [odxlinks.resolve(st_ref, State) for st_ref in self.pre_condition_state_refs])
        self._state_transitions = NamedItemList(
            [odxlinks.resolve(stt_ref, StateTransition) for stt_ref in self.state_transition_refs])

        if self.admin_data:
            self.admin_data._resolve_odxlinks(odxlinks)

        if self.audience:
            self.audience._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.admin_data:
            self.admin_data._resolve_snrefs(diag_layer)

        if self.audience:
            self.audience._resolve_snrefs(diag_layer)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

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

        if len(coding_objects) != 1:
            raise DecodeError(
                f"The service {self.short_name} cannot decode the message {raw_message.hex()}")
        coding_object = coding_objects[0]
        param_dict = coding_object.decode(raw_message)
        if not isinstance(param_dict, dict):
            # if this happens, this is probably due to a bug in
            # coding_object.decode()
            raise RuntimeError(f"Expected a set of decoded parameters, got {type(param_dict)}")
        return Message(
            coded_message=raw_message,
            service=self,
            coding_object=coding_object,
            param_dict=param_dict)

    def encode_request(self, **params: ParameterValue) -> bytes:
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
        if self.request is None:
            return b''

        missing_params = {x.short_name
                          for x in self.request.required_parameters}.difference(params.keys())
        odxassert(not missing_params, f"The parameters {missing_params} are required but missing!")

        # make sure that no unknown parameters are specified
        rq_all_param_names = {x.short_name for x in self.request.parameters}
        odxassert(
            set(params.keys()).issubset(rq_all_param_names),
            f"Unknown parameters specified for encoding: {params.keys()}, "
            f"known parameters are: {rq_all_param_names}")
        return self.request.encode(coded_request=None, **params)

    def encode_positive_response(self,
                                 coded_request: bytes,
                                 response_index: int = 0,
                                 **params: ParameterValue) -> bytes:
        # TODO: Should the user decide the positive response or what are the differences?
        return self.positive_responses[response_index].encode(coded_request, **params)

    def encode_negative_response(self,
                                 coded_request: bytes,
                                 response_index: int = 0,
                                 **params: ParameterValue) -> bytes:
        return self.negative_responses[response_index].encode(coded_request, **params)

    def __call__(self, **params: ParameterValue) -> bytes:
        """Encode a request."""
        return self.encode_request(**params)

    def __hash__(self) -> int:
        return hash(self.odx_id)

    def __eq__(self, o: Any) -> bool:
        return isinstance(o, DiagService) and self.odx_id == o.odx_id
