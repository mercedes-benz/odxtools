from typing import List
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .comparam import Comparam
from .complexcomparam import ComplexComparam
from .odxlink import OdxDocFragment


def create_any_comparam_from_et(et_element: ElementTree.Element,
                                doc_frags: List[OdxDocFragment]) -> BaseComparam:
    if et_element.tag == "COMPARAM":
        return Comparam.from_et(et_element, doc_frags)
    elif et_element.tag == "COMPLEX-COMPARAM":
        return ComplexComparam.from_et(et_element, doc_frags)

    raise RuntimeError(f"Unhandled communication parameter type {et_element.tag}")
