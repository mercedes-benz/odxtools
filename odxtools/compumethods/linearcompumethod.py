# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
from ..odxtypes import AtomicOdxType, DataType
from .compumethod import CompuMethod, CompuMethodCategory
from .limit import Limit


@dataclass
class LinearCompuMethod(CompuMethod):
    """Represents the decoding function d(y) = (offset + factor * y) / denominator
    where d(y) is the physical value and y is the internal value.

    Examples
    --------

    Define the decoding function `d(y) = 4+2*y` (or equivalent encoding `e(x) = floor((x-4)/2)`)
    on all integers `y` in the range -10..10 (and `x` in -16..25).

    ```python
    method = LinearCompuMethod(
        offset=4,
        factor=2,
        internal_type=DataType.A_INT32,
        physical_type=DataType.A_INT32,
        internal_lower_limit = Limit(-10, IntervalType.CLOSED),
        internal_upper_limit = Limit(11, IntervalType.OPEN)
    )
    ```

    Decode an internal value:

    ```python
    >>> method.convert_internal_to_physical(6)  # == 4+2*6
    16
    ```

    Encode a physical value:

    ```python
    >>> method.convert_physical_to_internal(6)  # == 6/2-2
    1
    ```

    Get physical limits:

    ```python
    >>> method.physical_lower_limit
    Limit(value=-16, interval_type=IntervalType.CLOSED)
    >>> method.physical_upper_limit
    Limit(value=26, interval_type=IntervalType.OPEN)
    ```

    (Note that there may be additional restrictions to valid physical values by the surrounding data object prop.
    For example, limits given by the bit length are not considered in the compu method.)
    """

    offset: float
    factor: float
    denominator: float
    internal_lower_limit: Optional[Limit]
    internal_upper_limit: Optional[Limit]

    def __post_init__(self) -> None:
        odxassert(self.denominator > 0)

        self.__compute_physical_limits()

    @property
    def category(self) -> CompuMethodCategory:
        return "LINEAR"

    @property
    def physical_lower_limit(self) -> Optional[Limit]:
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self) -> Optional[Limit]:
        return self._physical_upper_limit

    def __compute_physical_limits(self) -> None:
        """Computes the physical limits and stores them in the properties
        self._physical_lower_limit and self._physical_upper_limit.
        This method is only called during the initialization of a LinearCompuMethod.
        """

        def convert_internal_to_physical_limit(internal_limit: Optional[Limit],
                                               is_upper_limit: bool) -> Optional[Limit]:
            """Helper method

            Parameters:

            internal_limit
                the internal limit to be converted to a physical limit
            is_upper_limit
                True iff limit is the internal upper limit
            """
            if internal_limit is None or internal_limit.value_raw is None:
                return None

            internal_value = self.internal_type.from_string(internal_limit.value_raw)
            physical_value = self._convert_internal_to_physical(internal_value)

            result = Limit(
                value_raw=str(physical_value),
                value_type=self.physical_type,
                interval_type=internal_limit.interval_type)

            return result

        self._physical_lower_limit = None
        self._physical_upper_limit = None

        if self.factor >= 0:
            self._physical_lower_limit = convert_internal_to_physical_limit(
                self.internal_lower_limit, False)
            self._physical_upper_limit = convert_internal_to_physical_limit(
                self.internal_upper_limit, True)
        else:
            # If the factor is negative, the lower and upper limit are swapped
            self._physical_lower_limit = convert_internal_to_physical_limit(
                self.internal_upper_limit, True)
            self._physical_upper_limit = convert_internal_to_physical_limit(
                self.internal_lower_limit, False)

    def _convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if not isinstance(internal_value, (int, float)):
            raise DecodeError(f"The type of internal values of linear compumethods must "
                              f"either int or float (is: {type(internal_value).__name__})")

        if self.denominator is None:
            result = self.offset + self.factor * internal_value
        else:
            result = (self.offset + self.factor * internal_value) / self.denominator

        if self.physical_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
        ]:
            result = round(result)

        return self.physical_type.make_from(result)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        odxassert(self.is_valid_internal_value(internal_value))
        return self._convert_internal_to_physical(internal_value)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        if not isinstance(physical_value, (int, float)):
            odxraise(
                "The type of physical values of linear compumethods must "
                "either int or float", EncodeError)
            return 0

        odxassert(
            self.is_valid_physical_value(physical_value),
            f"physical value {physical_value} of type {type(physical_value)} "
            f"is not valid. Expected type {self.physical_type} with internal "
            f"range {self.internal_lower_limit} to {self.internal_upper_limit}")
        if self.denominator is None:
            result = (physical_value - self.offset) / self.factor
        else:
            result = ((physical_value * self.denominator) - self.offset) / self.factor

        if self.internal_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
        ]:
            result = round(result)
        return self.internal_type.make_from(result)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        # Do type checks
        expected_type = self.physical_type.python_type
        if issubclass(expected_type, float):
            if not isinstance(physical_value, (int, float)):
                return False
        else:
            if not isinstance(physical_value, expected_type):
                return False

        # Check the limits
        if self.physical_lower_limit is not None and not self.physical_lower_limit.complies_to_lower(
                physical_value):
            return False
        if self.physical_upper_limit is not None and not self.physical_upper_limit.complies_to_upper(
                physical_value):
            return False

        return True

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        # Do type checks
        expected_type = self.internal_type.python_type
        if issubclass(expected_type, float):
            if not isinstance(internal_value, (int, float)):
                return False
        else:
            if not isinstance(internal_value, expected_type):
                return False

        # Check the limits
        if self.internal_lower_limit is not None and not self.internal_lower_limit.complies_to_lower(
                internal_value):
            return False
        if self.internal_upper_limit is not None and not self.internal_upper_limit.complies_to_upper(
                internal_value):
            return False

        return True
