# SPDX-License-Identifier: MIT
from typing import List

from .diaglayers.basevariant import BaseVariant
from .variantmatcher import VariantMatcher


class BaseVariantMatcher(VariantMatcher):
    """BaseVariantMatcher implements the matching algorithm of base variants using
    BASE-VARIANT-PATTERNs according to ISO 22901-1.

    Usage (example):

    ```python

    # initialize the matcher with a list of base variants
    matcher = BaseVariantMatcher(candidates=[...], use_cache=use_cache)

    # run the request loop to obtain responses for every request
    for use_physical_addressing, encoded_request in matcher.request_loop():
        if use_physical_addressing:
            resp = send_to_ecu_using_physical_addressing(encoded_request)
        else:
            resp = send_to_ecu_using_functional_addressing(encoded_request)
        matcher.evaluate(resp)

    # result
    if matcher.has_match()
        matching_bv = matcher.matching_variant
        assert isinstance(matching_bv, BaseVariant)
    ```
    """

    def __init__(self, candidates: List[BaseVariant], use_cache: bool = True):
        super().__init__(candidates, use_cache)
