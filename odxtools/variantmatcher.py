# SPDX-License-Identifier: MIT
from collections.abc import Generator
from copy import copy
from enum import Enum

from .diaglayers.basevariant import BaseVariant
from .diaglayers.ecuvariant import EcuVariant
from .exceptions import DecodeError, odxraise
from .matchingparameter import MatchingParameter
from .response import Response


class VariantMatcher:
    """VariantMatcher implements the matching algorithm of ECU and
    base variants according to their ECU-VARIANT-PATTERNs or
    BASE-VARIANT-PATTERNs according to ISO 22901-1.

        Usage (example):

    ```python

    # initialize the matcher with a list of base or ECU variants
    matcher = VariantMatcher(candidates=[...], use_cache=use_cache)

    # run the request loop to obtain responses for every request
    for use_physical_addressing, encoded_request in matcher.request_loop():
        if use_physical_addressing:
            resp = send_to_ecu_using_physical_addressing(encoded_request)
        else:
            resp = send_to_ecu_using_functional_addressing(encoded_request)
        matcher.evaluate(resp)

    # result
    if matcher.has_match():
        if isinstance(matcher.matching_variant, BaseVariant):
            print(f"Match found for base variant "
                  f"{matcher.matching_variant.short_name}")
        elif isinstance(matcher.matching_variant, EcuVariant):
            print(f"Match found for ECU variant "
                  f"{matcher.matching_variant.short_name}")
        else:
            print(f"Match found for unknown diag layer type "
                  f"{type(matcher.matching_variant).__name__}")
    else:
        print("No matching base- or ECU variant found")
    ```

    TODO: Note that only patterns that exclusivly reference diagnostic
    services (i.e., no single-ECU jobs) in their matching parameters
    are currently supported.
    """

    class State(Enum):
        PENDING = 0
        NO_MATCH = 1
        MATCH = 2

    def __init__(self,
                 variant_candidates: list[EcuVariant] | list[BaseVariant],
                 use_cache: bool = True):

        self.variant_candidates = variant_candidates
        self.use_cache = use_cache
        self.req_resp_cache: dict[bytes, bytes] = {}
        self._recent_ident_response: bytes | None = None

        self._state = VariantMatcher.State.PENDING
        self._matching_variant: EcuVariant | BaseVariant | None = None

    def request_loop(self) -> Generator[tuple[bool, bytes], None, None]:
        """The request loop yielding tuples of byte sequences of
        requests and the whether physical addressing ought to be used
        to send them

        Each of these requests needs to be send to the ECU to be
        identified using the specified addressing scheme. The response
        of the ECU is then required to be passed to the matcher using
        the `evaluate()` method.
        """
        from .basevariantpattern import BaseVariantPattern
        from .ecuvariantpattern import EcuVariantPattern
        from .matchingbasevariantparameter import MatchingBaseVariantParameter

        if not self.is_pending():
            return

        self._matching_variant = None
        for variant in self.variant_candidates:
            variant_patterns: list[EcuVariantPattern] | list[BaseVariantPattern]
            if isinstance(variant, EcuVariant):
                variant_patterns = variant.ecu_variant_patterns
            elif isinstance(variant, BaseVariant):
                if variant.base_variant_pattern is None:
                    variant_patterns = []
                else:
                    variant_patterns = [variant.base_variant_pattern]
            else:
                odxraise(f"Only EcuVariant and BaseVariant are supported "
                         f"for pattern matching, not {type(self).__name__}")
                self._state = VariantMatcher.State.NO_MATCH
                return

            any_pattern_matches = False
            for pattern in variant_patterns:
                all_params_match = True
                for matching_param in pattern.get_matching_parameters():
                    req_bytes = matching_param.get_ident_service(variant).encode_request()

                    if self.use_cache and req_bytes in self.req_resp_cache:
                        resp_values = copy(self.req_resp_cache[req_bytes])
                    else:
                        if isinstance(matching_param, MatchingBaseVariantParameter):
                            yield matching_param.use_physical_addressing, req_bytes
                        else:
                            yield True, req_bytes
                        resp_values = self._get_ident_response()
                        self._update_cache(req_bytes, copy(resp_values))

                    cur_response_matches = self._ident_response_matches(
                        variant, matching_param, resp_values)
                    all_params_match = all_params_match and cur_response_matches
                    if not all_params_match:
                        break

                if all_params_match:
                    any_pattern_matches = True
                    break

            if any_pattern_matches:
                self._state = VariantMatcher.State.MATCH
                self._matching_variant = variant
                break

        if self.is_pending():
            # no pattern has matched for any ecu variant
            self._state = VariantMatcher.State.NO_MATCH

    def evaluate(self, resp_bytes: bytes) -> None:
        """Update the matcher with the response to a requst.

        Warning: Use this method EXACTLY once within the loop body of the request loop.
        """
        self._recent_ident_response = bytes(resp_bytes)

    def is_pending(self) -> bool:
        """True iff request loop has not yet been run."""
        return self._state == VariantMatcher.State.PENDING

    def has_match(self) -> bool:
        """Returns true iff the non-pending matcher found a matching ecu variant.

        Raises a runtime error if the matcher is pending.
        """
        if self.is_pending():
            raise RuntimeError(
                "EcuVariantMatcher is pending. Run the request_loop to determine the active ecu variant."
            )
        return self._state == VariantMatcher.State.MATCH

    @property
    def matching_variant(self) -> EcuVariant | BaseVariant | None:
        """Returns the matched, i.e., active ecu variant if such a variant has been found."""
        return self._matching_variant

    def _ident_response_matches(
        self,
        variant: EcuVariant | BaseVariant,
        matching_param: MatchingParameter,
        response_bytes: bytes,
    ) -> bool:
        """Decode a binary response and extract the identification string according
        to the snref or snpathref of the matching_param.
        """
        service = matching_param.get_ident_service(variant)

        # ISO 22901 requires that snref or snpathref is resolvable in
        # at least one POS-RESPONSE or NEG-RESPONSE
        all_responses: list[Response] = []
        all_responses.extend(service.positive_responses)
        all_responses.extend(service.negative_responses)
        all_responses.extend(variant.global_negative_responses)

        for cur_response in all_responses:
            try:
                decoded_vals = cur_response.decode(response_bytes)
            except DecodeError:
                # the current response object could not decode the received
                # data. Ignore it.
                continue

            if not matching_param.matches(decoded_vals):
                # This particular response object does not match the
                # expected value of the specified matching
                # parameter. Ignore it.
                continue

            return True

        return False

    def _update_cache(self, req_bytes: bytes, resp_bytes: bytes) -> None:
        if self.use_cache:
            self.req_resp_cache[req_bytes] = resp_bytes

    def _get_ident_response(self) -> bytes:
        if not self._recent_ident_response:
            raise RuntimeError(
                "No response available. Did you forget to call 'evaluate()' in a loop?")
        return self._recent_ident_response
