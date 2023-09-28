# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from xml.etree import ElementTree

from ..exceptions import odxassert, odxraise, odxrequire
from ..odxtypes import AtomicOdxType, DataType


class IntervalType(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    INFINITE = "INFINITE"


@dataclass
class Limit:
    value: AtomicOdxType
    interval_type: IntervalType = IntervalType.CLOSED

    def __post_init__(self) -> None:
        if self.interval_type == IntervalType.INFINITE:
            self.value = 0

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element], *,
                internal_type: DataType) -> Optional["Limit"]:

        if et_element is None:
            return None

        if (interval_type_str := et_element.get("INTERVAL-TYPE")) is not None:
            try:
                interval_type = IntervalType(interval_type_str)
            except ValueError:
                interval_type = IntervalType.CLOSED
                odxraise(f"Encountered unknown interval type '{interval_type_str}'")
        else:
            interval_type = IntervalType.CLOSED

        if interval_type == IntervalType.INFINITE:
            if et_element.tag == "LOWER-LIMIT":
                return Limit(float("-inf"), interval_type)
            else:
                odxassert(et_element.tag == "UPPER-LIMIT")
                return Limit(float("inf"), interval_type)
        elif internal_type == DataType.A_BYTEFIELD:
            hex_text = odxrequire(et_element.text)
            if len(hex_text) % 2 == 1:
                hex_text = "0" + hex_text
            return Limit(bytes.fromhex(hex_text), interval_type)
        else:
            return Limit(internal_type.from_string(odxrequire(et_element.text)), interval_type)

    def complies_to_upper(self, value: AtomicOdxType) -> bool:
        """Checks if the value is in the range w.r.t. the upper limit.

        * If the interval type is closed, return `value <= limit.value`.
        * If the interval type is open, return `value < limit.value`.
        * If the interval type is infinite, return `True`.
        """
        if self.interval_type == IntervalType.CLOSED:
            return value <= self.value  # type: ignore[operator]
        elif self.interval_type == IntervalType.OPEN:
            return value < self.value  # type: ignore[operator]
        elif self.interval_type == IntervalType.INFINITE:
            return True

    def complies_to_lower(self, value: AtomicOdxType) -> bool:
        """Checks if the value is in the range w.r.t. the lower limit.

        * If the interval type is closed, return `limit.value <= value`.
        * If the interval type is open, return `limit.value < value`.
        * If the interval type is infinite, return `True`.
        """
        if self.interval_type == IntervalType.CLOSED:
            return self.value <= value  # type: ignore[operator]
        elif self.interval_type == IntervalType.OPEN:
            return self.value < value  # type: ignore[operator]
        elif self.interval_type == IntervalType.INFINITE:
            return True
