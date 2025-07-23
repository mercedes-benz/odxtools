# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxraise
from .identvaluetype import IdentValueType
from .odxdoccontext import OdxDocContext
from .odxtypes import AtomicOdxType, DataType


@dataclass(kw_only=True)
class IdentValue:
    """
    Corresponds to IDENT-VALUE.
    """

    value_raw: str

    # note that the spec says this attribute is named "TYPE", but in
    # python, "type" is a build-in function...
    value_type: IdentValueType

    @property
    def value(self) -> AtomicOdxType:
        return self._value

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "IdentValue":
        value_raw = et_element.text or ""

        try:
            value_type = IdentValueType(et_element.attrib["TYPE"])
        except Exception as e:
            odxraise(f"Cannot parse IDENT-VALUE-TYPE: {e}")
            value_type = None

        return IdentValue(value_raw=value_raw, value_type=value_type)

    def __post_init__(self) -> None:
        self._data_type = DataType(self.value_type.value)
        self._value = self._data_type.from_string(self.value_raw.strip())
