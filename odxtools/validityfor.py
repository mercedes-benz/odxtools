# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxtypes import AtomicOdxType, DataType
from .sessionsubelemtype import SessionSubElemType


@dataclass(kw_only=True)
class ValidityFor:
    value_raw: str
    value_type: SessionSubElemType

    @property
    def value(self) -> AtomicOdxType:
        return self._value

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ValidityFor":
        value_raw = et_element.text or ""

        value_type_str = odxrequire(et_element.get("TYPE"))
        try:
            value_type = SessionSubElemType(value_type_str)
        except ValueError:
            value_type = cast(SessionSubElemType, None)
            odxraise(f"Encountered unknown SESSION-SUB-ELEM-TYPE type '{value_type_str}'")

        return ValidityFor(
            value_raw=value_raw,
            value_type=value_type,
        )

    def __post_init__(self) -> None:
        self._data_type = DataType(self.value_type.value)
        self._value = self._data_type.from_string(self.value_raw.strip())
