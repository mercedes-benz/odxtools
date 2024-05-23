# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from ..odxtypes import AtomicOdxType, DataType


@dataclass
class CompuConst:
    v: Optional[str]
    vt: Optional[str]

    data_type: DataType

    @staticmethod
    def compuvalue_from_et(et_element: ElementTree.Element, *, data_type: DataType) -> "CompuConst":

        v = et_element.findtext("V")
        vt = et_element.findtext("VT")

        return CompuConst(v=v, vt=vt, data_type=data_type)

    def __post_init__(self) -> None:
        self._value: Optional[AtomicOdxType] = self.vt
        if self.v is not None:
            self._value = self.data_type.from_string(self.v)

    @property
    def value(self) -> Optional[AtomicOdxType]:
        return self._value
