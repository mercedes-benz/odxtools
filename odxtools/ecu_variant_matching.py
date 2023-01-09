# SPDX-License-Identifier: MIT
# Copyright (c) 2023 MBition GmbH

from enum import Enum
from typing import ByteString, Dict, List, Optional, Union

from odxtools.diaglayer import DiagLayer
from odxtools.diaglayertype import DIAG_LAYER_TYPE
from odxtools.ecu_variant_patterns import MatchingParameter
from odxtools.service import DiagService


class EcuVariantMatcher:

    class State(Enum):
        PENDING = 0
        NO_MATCH = 1
        MATCH = 2

    @staticmethod
    def get_ident_service(diag_layer: DiagLayer, matching_param: MatchingParameter) -> DiagService:
        service_name = matching_param.diag_comm_snref
        # TODO this is not working since NamedItemList.__contains__() is not implemented
        #assert service_name in diag_layer.services
        service = diag_layer.services[service_name]
        assert isinstance(service, DiagService)
        return service

    @staticmethod
    def encode_ident_request(diag_layer: DiagLayer, matching_param: MatchingParameter) -> bytearray:
        service = EcuVariantMatcher.get_ident_service(diag_layer, matching_param)
        return service.encode_request()

    @staticmethod
    def decode_ident_response(diag_layer: DiagLayer, matching_param: MatchingParameter, response: bytearray) -> str:
        service = EcuVariantMatcher.get_ident_service(diag_layer, matching_param)
        assert service.positive_responses is not None
        resp_decoded = service.positive_responses[0].decode(response)
        assert matching_param.out_param_if_snref in resp_decoded
        return resp_decoded[matching_param.out_param_if_snref]

    def __init__(self, ecu_variant_candidates: List[DiagLayer], use_cache: bool = True):
        
        self.ecus = ecu_variant_candidates
        for ecu in self.ecus:
            assert ecu.variant_type == DIAG_LAYER_TYPE.ECU_VARIANT

        self.use_cache = use_cache
        self.req_resp_cache: Dict[ByteString, Union[bytes, bytearray]] = {}
        self._recent_ident_response: Optional[Union[bytes, bytearray]] = None

        self._state = EcuVariantMatcher.State.PENDING

    def request_loop(self):
        if not self.is_pending():
            return

        for ecu in self.ecus:
            any_match = False
            for pattern in ecu.ecu_variant_patterns:
                all_match = True
                for matching_param in pattern.matching_parameters:
                    req_bytes = EcuVariantMatcher.encode_ident_request(ecu, matching_param)
                    if self.use_cache and bytes(req_bytes) in self.req_resp_cache:
                        resp_bytes = self.req_resp_cache[bytes(req_bytes)]
                    else:
                        yield req_bytes
                        resp_bytes = self._get_ident_response()
                        self._update_cache(req_bytes, resp_bytes)
                    ident_val = EcuVariantMatcher.decode_ident_response(ecu, matching_param, resp_bytes)
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

    def evaluate(self, resp_bytes: bytearray) -> None:
        self._recent_ident_response = resp_bytes

    def is_pending(self) -> bool:
        return self._state == EcuVariantMatcher.State.PENDING

    def has_match(self) -> bool:
        if self.is_pending():
            raise RuntimeError("EcuVariantMatcher is pending. Run the request_loop to determine the active ecu variant.")
        return self._state == EcuVariantMatcher.State.MATCH

    def get_active_ecu_variant(self) -> DiagLayer:
        assert self.has_match()
        return self._match

    def _update_cache(self, req_bytes: bytearray, resp_bytes: bytearray):
        if self.use_cache:
            self.req_resp_cache[bytes(req_bytes)] = resp_bytes

    def _get_ident_response(self):
        if not self._recent_ident_response:
            raise RuntimeError("No response available. Mayby forgot to call 'evaluate' in loop?")
        return self._recent_ident_response