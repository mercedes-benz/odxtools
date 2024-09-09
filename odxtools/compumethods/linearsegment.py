# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional, Union

from ..exceptions import odxraise, odxrequire
from ..odxtypes import AtomicOdxType, DataType
from .compuscale import CompuScale
from .limit import Limit


@dataclass
class LinearSegment:
    """Helper class to represent a segment of a piecewise-linear interpolation.

    Multiple compu methods (LINEAR, SCALE-LINEAR, TAB-INTP) require
    linear interpolation. This class centralizes the required
    parameters for a single such segment. (The required parameters are
    extracted from the respective compu method's
    COMPU-INTERNAL-TO-PHYS objects. We do it this way because the
    internal-to-phys objects are rather clunky to work with and
    feature a lot of irrelevant information.)

    """
    offset: float
    factor: float
    denominator: float
    internal_lower_limit: Optional[Limit]
    internal_upper_limit: Optional[Limit]

    inverse_value: Union[int, float]  # value used as inverse if factor is 0

    internal_type: DataType
    physical_type: DataType

    @staticmethod
    def from_compu_scale(scale: CompuScale, *, internal_type: DataType,
                         physical_type: DataType) -> "LinearSegment":
        coeffs = odxrequire(scale.compu_rational_coeffs)

        offset = coeffs.numerators[0]
        factor = 0 if len(coeffs.numerators) == 1 else coeffs.numerators[1]

        denominator = 1.0
        if len(coeffs.denominators) > 0:
            denominator = coeffs.denominators[0]

        inverse_value: Union[int, float] = 0
        if scale.compu_inverse_value is not None:
            x = odxrequire(scale.compu_inverse_value).value
            if not isinstance(x, (int, float)):
                odxraise(f"Non-numeric COMPU-INVERSE-VALUE specified ({x!r})")
            inverse_value = x

        internal_lower_limit = scale.lower_limit
        internal_upper_limit = scale.upper_limit

        return LinearSegment(
            offset=offset,
            factor=factor,
            denominator=denominator,
            internal_lower_limit=internal_lower_limit,
            internal_upper_limit=internal_upper_limit,
            inverse_value=inverse_value,
            internal_type=internal_type,
            physical_type=physical_type)

    @property
    def physical_lower_limit(self) -> Optional[Limit]:
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self) -> Optional[Limit]:
        return self._physical_upper_limit

    def __post_init__(self) -> None:
        self.__compute_physical_limits()

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> Union[float, int]:
        if not isinstance(internal_value, (int, float)):
            odxraise(f"Internal values of linear compumethods must "
                     f"either be int or float (is: {type(internal_value).__name__})")

        result = (self.offset + self.factor * internal_value) / self.denominator

        if self.physical_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
        ]:
            result = round(result)

        return result

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> Union[float, int]:
        if not isinstance(physical_value, (int, float)):
            odxraise(f"Physical values of linear compumethods must "
                     f"either be int or float (is: {type(physical_value).__name__})")

        if abs(self.factor) < 1e-10:
            # "If factor = 0 then COMPU-INVERSE-VALUE shall be specified.
            return self.inverse_value

        result = (physical_value * self.denominator - self.offset) / self.factor

        if self.internal_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
        ]:
            result = round(result)

        return result

    def __compute_physical_limits(self) -> None:
        """Computes the physical limits and stores them in the properties
        self._physical_lower_limit and self._physical_upper_limit.
        This method is called by `__post_init__()`.
        """

        def convert_internal_to_physical_limit(internal_limit: Optional[Limit]) -> Optional[Limit]:
            """Helper method to convert a single internal limit
            """
            if internal_limit is None or internal_limit.value_raw is None:
                return None

            internal_value = self.internal_type.from_string(internal_limit.value_raw)
            physical_value = self.convert_internal_to_physical(internal_value)

            result = Limit(
                value_raw=str(physical_value),
                value_type=self.physical_type,
                interval_type=internal_limit.interval_type)

            return result

        self._physical_lower_limit = None
        self._physical_upper_limit = None

        if self.factor >= 0:
            self._physical_lower_limit = convert_internal_to_physical_limit(
                self.internal_lower_limit)
            self._physical_upper_limit = convert_internal_to_physical_limit(
                self.internal_upper_limit)
        else:
            # If the scaling factor is negative, the lower and upper
            # limit are swapped
            self._physical_lower_limit = convert_internal_to_physical_limit(
                self.internal_upper_limit)
            self._physical_upper_limit = convert_internal_to_physical_limit(
                self.internal_lower_limit)

    def physical_applies(self, physical_value: AtomicOdxType) -> bool:
        """Returns True iff the segment is applicable to a given physical value"""
        # Do type checks
        expected_type = self.physical_type.python_type
        if issubclass(expected_type, float):
            if not isinstance(physical_value, (int, float)):
                return False
        else:
            if not isinstance(physical_value, expected_type):
                return False

        if self._physical_lower_limit is not None and \
           not self._physical_lower_limit.complies_to_lower(physical_value):
            return False

        if self._physical_upper_limit is not None and \
           not self._physical_upper_limit.complies_to_upper(physical_value):
            return False

        return True

    def internal_applies(self, internal_value: AtomicOdxType) -> bool:
        """Returns True iff the segment is applicable to a given internal value"""
        # Do type checks
        expected_type = self.internal_type.python_type
        if issubclass(expected_type, float):
            if not isinstance(internal_value, (int, float)):
                return False
        else:
            if not isinstance(internal_value, expected_type):
                return False

        if self.internal_lower_limit is not None and \
           not self.internal_lower_limit.complies_to_lower(internal_value):
            return False

        if self.internal_upper_limit is not None and \
           not self.internal_upper_limit.complies_to_upper(internal_value):
            return False

        return True
