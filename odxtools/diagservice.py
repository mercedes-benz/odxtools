# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .createsdgs import create_sdgs_from_et
from .exceptions import DecodeError, odxassert, odxrequire
from .message import Message
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .parameters.parameter import Parameter
from .request import Request
from .response import Response
from .specialdatagroup import SpecialDataGroup
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer
    from .endofpdufield import EndOfPduField


@dataclass
class DiagService:
    """Representation of a diagnostic service description.
    """

    odx_id: OdxLinkId
    short_name: str
    request_ref: OdxLinkRef
    pos_response_refs: List[OdxLinkRef]
    neg_response_refs: List[OdxLinkRef]
    long_name: Optional[str]
    admin_data: Optional[AdminData]
    description: Optional[str]
    semantic: Optional[str]
    audience: Optional[Audience]
    functional_class_refs: Iterable[OdxLinkRef]
    pre_condition_state_refs: Iterable[OdxLinkRef]
    state_transition_refs: Iterable[OdxLinkRef]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagService":

        # logger.info(f"Parsing service based on ET DiagService element: {et_element}")
        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
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
            odx_id=odx_id,
            short_name=short_name,
            request_ref=request_ref,
            pos_response_refs=pos_response_refs,
            neg_response_refs=neg_response_refs,
            long_name=long_name,
            description=description,
            admin_data=admin_data,
            semantic=semantic,
            audience=audience,
            functional_class_refs=functional_class_refs,
            pre_condition_state_refs=pre_condition_state_refs,
            state_transition_refs=state_transition_refs,
            sdgs=sdgs,
        )

    @property
    def request(self) -> Optional[Request]:
        return self._request

    @property
    def free_parameters(self) -> List[Union[Parameter, "EndOfPduField"]]:  # type: ignore
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

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._request = odxlinks.resolve(self.request_ref)

        self._positive_responses = NamedItemList[Response](short_name_as_id, [
            odxlinks.resolve(x, Response) for x in self.pos_response_refs
        ])

        self._negative_responses = NamedItemList[Response](short_name_as_id, [
            odxlinks.resolve(x, Response) for x in self.neg_response_refs
        ])

        self._functional_classes = NamedItemList(short_name_as_id, [
            odxlinks.resolve(fc_id) for fc_id in self.functional_class_refs
        ])
        self._pre_condition_states = NamedItemList(short_name_as_id, [
            odxlinks.resolve(st_id) for st_id in self.pre_condition_state_refs
        ])
        self._state_transitions = NamedItemList(short_name_as_id, [
            odxlinks.resolve(stt_id) for stt_id in self.state_transition_refs
        ])

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

    def decode_message(self, message: bytes) -> Message:

        # Check if message is a request or positive or negative response
        interpretable_message_types = []

        if (self.request is None or self.positive_responses is None or
                self.negative_responses is None):
            raise RuntimeError("References couldn't be resolved or have not been resolved yet."
                               " Try calling `database.resolve_odxlinks()`.")

        for message_type in [self.request, *self.positive_responses, *self.negative_responses]:
            prefix = message_type.coded_const_prefix(
                request_prefix=self.request.coded_const_prefix())
            if all(b == message[i] for (i, b) in enumerate(prefix)):
                interpretable_message_types.append(message_type)

        if len(interpretable_message_types) != 1:
            raise DecodeError(
                f"The service {self.short_name} cannot decode the message {message.hex()}")
        message_type = interpretable_message_types[0]
        param_dict = message_type.decode(message)
        return Message(
            coded_message=message, service=self, structure=message_type, param_dict=param_dict)

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
        missing_params = {x.short_name
                          for x in self.request.required_parameters}.difference(params.keys())
        odxassert(not missing_params, f"The parameters {missing_params} are required but missing!")

        # make sure that no unknown parameters are specified
        rq_all_param_names = {x.short_name for x in self.request.parameters}
        odxassert(
            set(params.keys()).issubset(rq_all_param_names),
            f"Unknown parameters specified for encoding: {params.keys()}, "
            f"known parameters are: {rq_all_param_names}")
        return self.request.encode(**params)

    def encode_positive_response(self, coded_request, response_index=0, **params):
        # TODO: Should the user decide the positive response or what are the differences?
        return self.positive_responses[response_index].encode(coded_request, **params)

    def encode_negative_response(self, coded_request, response_index=0, **params):
        return self.negative_responses[response_index].encode(coded_request, **params)

    def __call__(self, **params) -> bytes:
        """Encode a request."""
        return self.encode_request(**params)

    def __hash__(self) -> int:
        return hash(self.odx_id)

    def __eq__(self, o: object) -> bool:
        return isinstance(o, DiagService) and self.odx_id == o.odx_id
