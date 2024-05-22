# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from ..odxlink import OdxDocFragment
from .compuinversevalue import CompuInverseValue


@dataclass
class CompuDefaultValue:
    v: Optional[str]
    vt: Optional[str]

    compu_inverse_value: Optional[CompuInverseValue]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "CompuDefaultValue":
        v = et_element.findtext("V")
        vt = et_element.findtext("VT")

        compu_inverse_value = None
        if (civ_elem := et_element.find("COMPU-INVERSE-VALUE")) is not None:
            compu_inverse_value = CompuInverseValue.from_et(civ_elem, doc_frags)

        return CompuDefaultValue(v=v, vt=vt, compu_inverse_value=compu_inverse_value)
