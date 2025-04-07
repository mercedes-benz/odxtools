# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from ..odxtypes import AtomicOdxType, DataType


@dataclass(kw_only=True)
class CompuConst:
    v: str | None = None
    vt: str | None = None

    data_type: DataType

    @property
    def value(self) -> AtomicOdxType | None:
        return self._value

    @staticmethod
    def compuvalue_from_et(et_element: ElementTree.Element, *, data_type: DataType) -> "CompuConst":

        v = et_element.findtext("V")
        vt = et_element.findtext("VT")

        return CompuConst(v=v, vt=vt, data_type=data_type)

    def __post_init__(self) -> None:
        self._value: AtomicOdxType | None = self.vt
        if self.v is not None:
            self._value = self.data_type.from_string(self.v)
