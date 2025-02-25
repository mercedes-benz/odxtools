# SPDX-License-Identifier: MIT
from typing import List

from .diaglayers.ecuvariant import EcuVariant
from .variantmatcher import VariantMatcher


class EcuVariantMatcher(VariantMatcher):
    """EcuVariantMatcher implements the matching algorithm of ecu variants using
    ECU-VARIANT-PATTERNs according to ISO 22901-1.

    Usage (example):

    ```python

    # initialize the matcher with a list of ecu variants
    matcher = EcuVariantMatcher(ecu_variant_candidates=[...], use_cache=use_cache)

    # run the request loop to obtain responses for every request
    for _, encoded_request in matcher.request_loop():
        resp = send_to_ecu(encoded_request)
        matcher.evaluate(resp)

    # result
    if matcher.has_match()
        matching_ecu = matcher.matching_variant
        assert isinstance(matching_ecu, EcuVariant)
    ```
    """

    def __init__(self, ecu_variant_candidates: List[EcuVariant], use_cache: bool = True):
        super().__init__(ecu_variant_candidates, use_cache)
