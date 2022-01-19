# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from odxtools.audience import Audience, read_audience_from_odx
from odxtools.utils import read_description_from_odx
from odxtools.exceptions import DecodeError
from typing import List, Optional, Union
from .structures import Request, Response
from .nameditemlist import NamedItemList
from .message import Message


class DiagService:
    def __init__(self,
                 id,
                 short_name,
                 request,
                 positive_responses,
                 negative_responses,
                 long_name=None,
                 description=None,
                 semantic=None,
                 audience: Optional[Audience] = None,
                 functional_class_refs=[]):
        """Constructs the service.

        Parameters:
        ----------
        id: str
        short_name: str
            the short name of this DIAG-SERVICE
        request: str | Request
            the ID of a request or a object
        positive_responses: List[str] | List[Response]
        negative_responses: List[str] | List[Response]
        """
        self.id = id
        self.short_name = short_name
        if isinstance(request, str):
            self._request = None
            self.request_ref_id = request
        elif isinstance(request, Request):
            self._request = request
            self.request_ref_id = request
        else:
            raise ValueError(
                "request must be a string (the ID of a request) or a Request object")

        if all(isinstance(x, Response) for x in positive_responses):
            self._positive_responses = \
                NamedItemList[Response](lambda pr: pr.short_name,
                                        positive_responses)
            self.pos_res_ref_ids = [pr.id for pr in positive_responses]
        else:
            self._positive_responses = None
            self.pos_res_ref_ids = positive_responses

        if all(isinstance(x, Response) for x in negative_responses):
            NamedItemList[Response](lambda nr: nr.short_name,
                                    negative_responses)
            self.neg_res_ref_ids = [nr.id for nr in negative_responses]
        else:
            self._negative_responses = None
            self.neg_res_ref_ids = negative_responses

        self.long_name = long_name
        self.description = description
        self.semantic = semantic
        self.audience = audience
        self.functional_class_refs = functional_class_refs
        self._functional_classes = []

    @property
    def request(self) -> Request:
        return self._request

    @property
    def positive_responses(self) -> List[Response]:
        return self._positive_responses

    @property
    def negative_responses(self) -> List[Response]:
        return self._negative_responses

    @property
    def functional_classes(self):
        return self._functional_classes

    def _resolve_references(self, id_lookup):
        self._request = id_lookup.get(self.request_ref_id)
        self._positive_responses = \
            NamedItemList(
                lambda pr: pr.short_name,
                [id_lookup.get(pr_id) for pr_id in self.pos_res_ref_ids])
        self._negative_responses = \
            NamedItemList(
                lambda nr: nr.short_name,
                [id_lookup.get(pr_id) for pr_id in self.neg_res_ref_ids])
        self._functional_classes = \
            NamedItemList(
                lambda fc: fc.short_name,
                [id_lookup.get(fc_id) for fc_id in self.functional_class_refs])
        if self.audience:
            self.audience._resolve_references(id_lookup)

    def decode_message(self, message: Union[bytes, bytearray]) -> Message:

        # Check if message is a request or positive or negative response
        interpretable_message_types = list(filter(lambda r: all(b == message[i]
                                                                for (i, b) in enumerate(r.coded_const_prefix(
                                                                    request_prefix=self.request.coded_const_prefix()))),
                                                  [self.request, *self.positive_responses,
                                                   *self.negative_responses]
                                                  ))
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
        missing_params = set(map(
            lambda x: x.short_name, self.request.get_required_parameters())).difference(params.keys())
        assert not missing_params, f"The parameters {missing_params} are required but missing!"

        # make sure that no unknown parameters are specified
        rq_all_param_names = set(
            map(lambda x: x.short_name, self.request.parameters))
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
        return f"DiagService(id={self.id}, semantic={self.semantic})"

    def __repr__(self):
        return self.__str__()


def read_diag_service_from_odx(et_element):

    # logger.info(f"Parsing service based on ET DiagService element: {et_element}")
    short_name = et_element.find("SHORT-NAME").text
    id = et_element.get("ID")

    request_ref_id = et_element.find("REQUEST-REF").get("ID-REF")

    pos_res_ref_ids = [
        el.get("ID-REF") for el in et_element.iterfind("POS-RESPONSE-REFS/POS-RESPONSE-REF")
    ]
    neg_res_ref_ids = [
        el.get("ID-REF") for el in et_element.iterfind("NEG-RESPONSE-REFS/NEG-RESPONSE-REF")
    ]
    functional_class_ref_ids = [
        el.get("ID-REF") for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF")
    ]

    long_name = et_element.find(
        "LONG-NAME").text if et_element.find("LONG-NAME") is not None else None
    description = read_description_from_odx(et_element.find("DESC"))
    semantic = et_element.get("SEMANTIC")

    audience = read_audience_from_odx(et_element.find(
        "AUDIENCE")) if et_element.find("AUDIENCE") else None

    diag_service = DiagService(id,
                               short_name,
                               request_ref_id,
                               pos_res_ref_ids,
                               neg_res_ref_ids,
                               long_name=long_name,
                               description=description,
                               semantic=semantic,
                               audience=audience,
                               functional_class_refs=functional_class_ref_ids)
    return diag_service
