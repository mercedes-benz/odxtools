# SPDX-License-Identifier: MIT
from enum import Enum
from typing import Dict, Generator, List, Optional

from .diaglayer import DiagLayer
from .diaglayertype import DiagLayerType
from .diagservice import DiagService
from .exceptions import OdxError, odxassert
from .matchingparameter import MatchingParameter
from .odxtypes import ParameterValue
from .response import Response


class EcuVariantMatcher:
    """EcuVariantMatcher implements the matching algorithm of ecu variants according to their
    ECU-VARIANT-PATTERN according to ISO 22901-1.

    Usage (example):

    ```python

    # initialize the matcher with a list of ecu variants,
    # i.e., DiagLayer instances of variant_type == DiagLayerType.ECU-VARIANT
    matcher = EcuVariantMatcher(ecu_variant_candidates=[...], use_cache=use_cache)

    # run the request loop to obtain responses for every request
    for req in matcher.request_loop():
        resp = ... # make a UDS request
        matcher.evaluate(resp)

    # result
    if matcher.has_match()
        match = matcher.get_active_ecu_variant()
    ```
    """

    class State(Enum):
        PENDING = 0
        NO_MATCH = 1
        MATCH = 2

    @staticmethod
    def get_ident_service(diag_layer: DiagLayer, matching_param: MatchingParameter) -> DiagService:
        service_name = matching_param.diag_comm_snref
        odxassert(service_name in [x.short_name for x in diag_layer.services])
        service = diag_layer.services[service_name]
        odxassert(isinstance(service, DiagService))
        return service

    @staticmethod
    def encode_ident_request(diag_layer: DiagLayer, matching_param: MatchingParameter) -> bytes:
        service = EcuVariantMatcher.get_ident_service(diag_layer, matching_param)
        return bytes(service.encode_request())

    @staticmethod
    def decode_ident_response(
        diag_layer: DiagLayer,
        matching_param: MatchingParameter,
        response_bytes: bytes,
    ) -> str:
        """Decode a binary response and extract the identification string according
        to the snref or snpathref of the matching_param.
        """
        service = EcuVariantMatcher.get_ident_service(diag_layer, matching_param)

        # ISO 22901 requires that snref or snpathref is resolvable in at least one
        # POS-RESPONSE or NEG-RESPONSE
        pos_neg_responses: List[Response] = []
        if service.positive_responses is not None:
            pos_neg_responses.extend(service.positive_responses)
        if service.negative_responses is not None:
            pos_neg_responses.extend(service.negative_responses)

        for any_response in pos_neg_responses:
            decoded_val: Optional[ParameterValue] = any_response.decode(response_bytes)
            # disassemble snref / snpathref
            path_ref = matching_param.out_param_if.split(".")
            for ref in path_ref:
                if isinstance(decoded_val, dict) and ref in decoded_val:
                    decoded_val = decoded_val[ref]
                else:
                    decoded_val = None
                    break

            if decoded_val is not None:
                if isinstance(decoded_val, str) or isinstance(decoded_val, int):
                    return str(decoded_val)

        raise OdxError(f"The snref or snpathref '{matching_param.out_param_if}' is cannot be \
                resolved for any positive or negative response.")

    def __init__(self, ecu_variant_candidates: List[DiagLayer], use_cache: bool = True):

        self.ecus = ecu_variant_candidates
        for ecu in self.ecus:
            odxassert(ecu.variant_type == DiagLayerType.ECU_VARIANT)

        self.use_cache = use_cache
        self.req_resp_cache: Dict[bytes, bytes] = {}
        self._recent_ident_response: Optional[bytes] = None

        self._state = EcuVariantMatcher.State.PENDING

    def request_loop(self) -> Generator[bytes, None, None]:
        """The request loop yields byte sequences of requests, which shall be executed within the
        loop body. It is required to pass the response back to the matcher using the evaluate method.
        """
        if not self.is_pending():
            return

        for ecu in self.ecus:
            any_match = False
            for pattern in ecu.ecu_variant_patterns:
                all_match = True
                for matching_param in pattern.matching_parameters:
                    req_bytes = bytes(EcuVariantMatcher.encode_ident_request(ecu, matching_param))
                    if self.use_cache and req_bytes in self.req_resp_cache:
                        resp_bytes = self.req_resp_cache[req_bytes]
                    else:
                        yield req_bytes
                        resp_bytes = self._get_ident_response()
                        self._update_cache(req_bytes, resp_bytes)
                    ident_val = EcuVariantMatcher.decode_ident_response(
                        ecu, matching_param, resp_bytes)
                    all_match &= matching_param.is_match(ident_val)
                if all_match:
                    any_match = True
                    break
            if any_match:
                self._state = EcuVariantMatcher.State.MATCH
                self._match = ecu
                break
        if self.is_pending():
            # no pattern has matched for any ecu variant
            self._state = EcuVariantMatcher.State.NO_MATCH

    def evaluate(self, resp_bytes: bytes) -> None:
        """Update the matcher with the response to a requst.

        Warning: Use this method EXACTLY once within the loop body of the request loop.
        """
        self._recent_ident_response = bytes(resp_bytes)

    def is_pending(self) -> bool:
        """True iff request loop has not yet been run."""
        return self._state == EcuVariantMatcher.State.PENDING

    def has_match(self) -> bool:
        """Returns true iff the non-pending matcher found a matching ecu variant.

        Raises a runtime error if the matcher is pending.
        """
        if self.is_pending():
            raise RuntimeError(
                "EcuVariantMatcher is pending. Run the request_loop to determine the active ecu variant."
            )
        return self._state == EcuVariantMatcher.State.MATCH

    def get_active_ecu_variant(self) -> DiagLayer:
        """Returns the matched, i.e., active ecu variant if such a variant has been found."""
        odxassert(self.has_match())
        return self._match

    def _update_cache(self, req_bytes: bytes, resp_bytes: bytes) -> None:
        if self.use_cache:
            self.req_resp_cache[req_bytes] = resp_bytes

    def _get_ident_response(self) -> bytes:
        if not self._recent_ident_response:
            raise RuntimeError(
                "No response available. Did you forget to call 'evaluate()' in a loop?")
        return self._recent_ident_response
