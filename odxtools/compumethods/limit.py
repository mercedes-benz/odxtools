# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from enum import Enum
from typing import NamedTuple, Union


class IntervalType(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    INFINITE = "INFINITE"


class Limit(NamedTuple):
    value: Union[str, int, float, bytes]
    interval_type: IntervalType = IntervalType.CLOSED

    def complies_to_upper(self, value):
        """Checks if the value is in the range w.r.t. the upper limit.

        * If the interval type is closed, return `value <= limit.value`.
        * If the interval type is open, return `value < limit.value`.
        * If the interval type is infinite, return `True`.
        """
        if self.interval_type == IntervalType.CLOSED:
            return value <= self.value
        elif self.interval_type == IntervalType.OPEN:
            return value < self.value
        elif self.interval_type == IntervalType.INFINITE:
            return True

    def complies_to_lower(self, value):
        """Checks if the value is in the range w.r.t. the lower limit.

        * If the interval type is closed, return `limit.value <= value`.
        * If the interval type is open, return `limit.value < value`.
        * If the interval type is infinite, return `True`.
        """
        if self.interval_type == IntervalType.CLOSED:
            return self.value <= value
        elif self.interval_type == IntervalType.OPEN:
            return self.value < value
        elif self.interval_type == IntervalType.INFINITE:
            return True
