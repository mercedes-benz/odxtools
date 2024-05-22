# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from ..odxlink import OdxDocFragment


@dataclass
class CompuInverseValue:
    v: Optional[str]
    vt: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "CompuInverseValue":
        v = et_element.findtext("V")
        vt = et_element.findtext("VT")

        return CompuInverseValue(v=v, vt=vt)
