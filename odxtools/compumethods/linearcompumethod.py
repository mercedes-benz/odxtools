# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import Optional, Union

from ..odxtypes import DataType

from .compumethodbase import CompuMethod
from .limit import IntervalType, Limit


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

    def __init__(self,
                 offset,
                 factor,
                 internal_type: Union[DataType, str],
                 physical_type: Union[DataType, str],
                 denominator=1,
                 internal_lower_limit: Optional[Limit] = None,
                 internal_upper_limit: Optional[Limit] = None):
        super().__init__(internal_type, physical_type, "LINEAR")
        self.offset = offset
        self.factor = factor
        self.denominator = denominator

        self.internal_lower_limit = internal_lower_limit
        if internal_lower_limit is None or internal_lower_limit.interval_type == IntervalType.INFINITE:
            self.internal_lower_limit = Limit(float("-inf"),
                                              IntervalType.INFINITE)

        self.internal_upper_limit = internal_upper_limit
        if internal_upper_limit is None or internal_upper_limit.interval_type == IntervalType.INFINITE:
            self.internal_upper_limit = Limit(float("inf"),
                                              IntervalType.INFINITE)

        assert self.internal_lower_limit is not None and self.internal_upper_limit is not None
        assert denominator > 0 and isinstance(denominator, (int, float))

        self.__compute_physical_limits()

    @property
    def physical_lower_limit(self):
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self):
        return self._physical_upper_limit

    def __compute_physical_limits(self):
        """Computes the physical limits and stores them in the properties
        self._physical_lower_limit and self._physical_upper_limit.
        This method is only called during the initialization of a LinearCompuMethod.
        """
        def convert_to_limit_to_physical(limit: Limit, is_upper_limit: bool):
            """Helper method

            Parameters:

            limit
                the internal limit to be converted to a physical limit
            is_upper_limit
                True iff limit is the internal upper limit
            """
            assert isinstance(limit.value, (int, float))
            if limit.interval_type == IntervalType.INFINITE:
                return limit
            elif limit.interval_type == limit.interval_type.OPEN and self.internal_type.as_python_type() == int:
                closed_limit = limit.value - 1 if is_upper_limit else limit.value + 1
                return Limit(
                    value=self._convert_internal_to_physical(closed_limit),
                    interval_type=IntervalType.CLOSED
                )
            else:
                return Limit(
                    value=self._convert_internal_to_physical(limit.value),
                    interval_type=limit.interval_type
                )

        if self.factor >= 0:
            self._physical_lower_limit = convert_to_limit_to_physical(
                self.internal_lower_limit, False)
            self._physical_upper_limit = convert_to_limit_to_physical(
                self.internal_upper_limit, True)
        else:
            # If the factor is negative, the lower and upper limit are swapped
            self._physical_lower_limit = convert_to_limit_to_physical(
                self.internal_upper_limit, True)
            self._physical_upper_limit = convert_to_limit_to_physical(
                self.internal_lower_limit, False)

        if self.physical_type == DataType.A_UINT32:
            # If the data type is unsigned, the physical lower limit should be at least 0.
            if self._physical_lower_limit.interval_type == IntervalType.INFINITE or self._physical_lower_limit.value < 0:
                self._physical_lower_limit = Limit(
                    value=0,
                    interval_type=IntervalType.CLOSED
                )

    def _convert_internal_to_physical(self, internal_value):
        if self.denominator is None:
            result = self.offset + self.factor * internal_value
        else:
            result = (self.offset + self.factor *
                      internal_value) / self.denominator

        if self.internal_type == DataType.A_FLOAT64 and self.physical_type in [DataType.A_INT32, DataType.A_UINT32]:
            result = round(result)
        return self.physical_type.make_from(result)

    def convert_internal_to_physical(self, internal_value) \
        -> Union[int, float]:
        assert self.is_valid_internal_value(internal_value)
        return self._convert_internal_to_physical(internal_value)

    def convert_physical_to_internal(self, physical_value):
        assert self.is_valid_physical_value(
            physical_value), f"physical value {physical_value} of type {type(physical_value)} is not valid. Expected type {self.physical_type} with internal range {self.internal_lower_limit} to {self.internal_upper_limit}"
        if self.denominator is None:
            result = (physical_value - self.offset) / self.factor
        else:
            result = ((physical_value * self.denominator) -
                      self.offset) / self.factor

        if self.physical_type == DataType.A_FLOAT64 and self.internal_type in [DataType.A_INT32, DataType.A_UINT32]:
            result = round(result)
        return self.internal_type.make_from(result)

    def is_valid_physical_value(self, physical_value):
        # Do type checks
        expected_type = self.physical_type.as_python_type()
        if expected_type == float and type(physical_value) not in [int, float]:
            return False
        elif expected_type != float and type(physical_value) != expected_type:
            return False

        # Compare to the limits
        if not self.physical_lower_limit.complies_to_lower(physical_value):
            return False
        if not self.physical_upper_limit.complies_to_upper(physical_value):
            return False
        return True

    def is_valid_internal_value(self, internal_value):
        expected_type = self.internal_type.as_python_type()
        if expected_type == float and type(internal_value) not in [int, float]:
            return False
        elif expected_type != float and type(internal_value) != expected_type:
            return False

        if not self.internal_lower_limit.complies_to_lower(internal_value):
            return False
        if not self.internal_upper_limit.complies_to_upper(internal_value):
            return False

        return True
