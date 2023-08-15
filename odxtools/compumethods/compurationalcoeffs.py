# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from ..exceptions import odxrequire
from ..odxlink import OdxDocFragment


@dataclass
class CompuRationalCoeffs:
    numerators: List[float]
    denominators: List[float]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "CompuRationalCoeffs":
        numerators = [
            float(odxrequire(elem.text)) for elem in et_element.iterfind("COMPU-NUMERATOR/V")
        ]
        denominators = [
            float(odxrequire(elem.text)) for elem in et_element.iterfind("COMPU-DENOMINATOR/V")
        ]

        return CompuRationalCoeffs(numerators=numerators, denominators=denominators)
