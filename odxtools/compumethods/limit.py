# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, overload
from xml.etree import ElementTree

from ..exceptions import odxraise
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType, compare_odx_values


class IntervalType(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    INFINITE = "INFINITE"


@dataclass
class Limit:
    value_raw: Optional[str]
    value_type: Optional[DataType]
    interval_type: Optional[IntervalType]

    def __post_init__(self) -> None:
        self._value: Optional[AtomicOdxType] = None

        if self.value_type is not None:
            self.set_value_type(self.value_type)

    @staticmethod
    @overload
    def limit_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment],
                      value_type: Optional[DataType]) -> "Limit":
        ...

    @staticmethod
    @overload
    def limit_from_et(et_element: None, doc_frags: List[OdxDocFragment],
                      value_type: Optional[DataType]) -> None:
        ...

    @staticmethod
    def limit_from_et(et_element: Optional[ElementTree.Element], doc_frags: List[OdxDocFragment],
                      value_type: Optional[DataType]) -> Optional["Limit"]:

        if et_element is None:
            return None

        interval_type = None
        if (interval_type_str := et_element.get("INTERVAL-TYPE")) is not None:
            try:
                interval_type = IntervalType(interval_type_str)
            except ValueError:
                odxraise(f"Encountered unknown interval type '{interval_type_str}'")

        value_raw = et_element.text

        return Limit(value_raw=value_raw, interval_type=interval_type, value_type=value_type)

    def set_value_type(self, value_type: DataType) -> None:
        self.value_type = value_type
        if self.value_raw is not None:
            self._value = value_type.from_string(self.value_raw)

    @property
    def value(self) -> Optional[AtomicOdxType]:
        return self._value

    def complies_to_upper(self, value: AtomicOdxType) -> bool:
        """Checks if the value is in the range w.r.t. the upper limit.

        * If the interval type is closed, return `value <= limit.value`.
        * If the interval type is open, return `value < limit.value`.
        * If the interval type is infinite, return `True`.
        """
        if self._value is None:
            # if no value is specified, assume interval type INFINITE
            # (what are we supposed to compare against?)
            return True

        if self.interval_type is None or self.interval_type == IntervalType.CLOSED:
            # assume interval type CLOSED if a value was specified,
            # but no interval type
            return compare_odx_values(value, self._value) <= 0
        elif self.interval_type == IntervalType.OPEN:
            return compare_odx_values(value, self._value) < 0

        if self.interval_type != IntervalType.INFINITE:
            odxraise("Unhandled interval type {self.interval_type}")

        return True

    def complies_to_lower(self, value: AtomicOdxType) -> bool:
        """Checks if the value is in the range w.r.t. the lower limit.

        * If the interval type is closed, return `limit.value <= value`.
        * If the interval type is open, return `limit.value < value`.
        * If the interval type is infinite, return `True`.
        """

        if self._value is None:
            # if no value is specified, assume interval type INFINITE
            # (what are we supposed to compare against?)
            return True

        if self.interval_type is None or self.interval_type == IntervalType.CLOSED:
            # assume interval type CLOSED if a value was specified,
            # but no interval type
            return compare_odx_values(value, self._value) >= 0
        elif self.interval_type == IntervalType.OPEN:
            return compare_odx_values(value, self._value) > 0

        if self.interval_type != IntervalType.INFINITE:
            odxraise("Unhandled interval type {self.interval_type}")

        return True
