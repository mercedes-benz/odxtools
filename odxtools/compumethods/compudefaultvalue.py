# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from ..odxtypes import DataType
from ..utils import dataclass_fields_asdict
from .compuconst import CompuConst
from .compuinversevalue import CompuInverseValue


@dataclass
class CompuDefaultValue(CompuConst):
    compu_inverse_value: Optional[CompuInverseValue]

    @staticmethod
    def compuvalue_from_et(et_element: ElementTree.Element, *,
                           data_type: DataType) -> "CompuDefaultValue":
        kwargs = dataclass_fields_asdict(
            CompuConst.compuvalue_from_et(et_element, data_type=data_type))

        compu_inverse_value = None
        if (civ_elem := et_element.find("COMPU-INVERSE-VALUE")) is not None:
            compu_inverse_value = CompuInverseValue.compuvalue_from_et(
                civ_elem, data_type=data_type)

        return CompuDefaultValue(**kwargs, compu_inverse_value=compu_inverse_value)
