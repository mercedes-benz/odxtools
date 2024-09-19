# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional, Union

from ..exceptions import odxraise, odxrequire
from ..odxtypes import AtomicOdxType, DataType
from .compuscale import CompuScale
from .limit import Limit


@dataclass
class RatFuncSegment:
    """Helper class to represent a segment of a piecewise rational function.
    """
    value_type: DataType

    numerator_coeffs: List[Union[int, float]]
    denominator_coeffs: List[Union[int, float]]

    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]

    @staticmethod
    def from_compu_scale(scale: CompuScale, value_type: DataType) -> "RatFuncSegment":
        coeffs = odxrequire(scale.compu_rational_coeffs,
                            "Scales for rational functions must exhibit "
                            "COMPU-RATIONAL-COEFFS")

        numerator_coeffs = coeffs.numerators
        denominator_coeffs = coeffs.denominators

        lower_limit = scale.lower_limit
        upper_limit = scale.upper_limit

        return RatFuncSegment(
            numerator_coeffs=numerator_coeffs,
            denominator_coeffs=denominator_coeffs,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            value_type=scale.range_type)

    def convert(self, value: AtomicOdxType) -> Union[float, int]:
        if not isinstance(value, (int, float)):
            odxraise(f"Internal values of linear compumethods must "
                     f"either be int or float (is: {type(value).__name__})")

        numerator = 0.0
        x = float(value)
        for numerator_coeff in reversed(self.numerator_coeffs):
            numerator *= x
            numerator += float(numerator_coeff)

        denominator = 0.0
        for denominator_coeff in reversed(self.denominator_coeffs):
            denominator *= x
            denominator += float(denominator_coeff)

        result = numerator / denominator

        if self.value_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
        ]:
            result = round(result)

        return result

    def applies(self, value: AtomicOdxType) -> bool:
        """Returns True iff the segment is applicable to a given internal value"""
        # Do type checks
        expected_type = self.value_type.python_type
        if issubclass(expected_type, float):
            if not isinstance(value, (int, float)):
                return False
        else:
            if not isinstance(value, expected_type):
                return False

        if self.lower_limit is not None and \
           not self.lower_limit.complies_to_lower(value):
            return False

        if self.upper_limit is not None and \
           not self.upper_limit.complies_to_upper(value):
            return False

        return True
