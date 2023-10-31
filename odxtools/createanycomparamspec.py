from typing import List, Union
from xml.etree import ElementTree

from .comparamspec import ComparamSpec
from .complexcomparamspec import ComplexComparamSpec
from .odxlink import OdxDocFragment


def create_any_comparam_spec_from_et(et_element: ElementTree.Element,
                                     doc_frags: List[OdxDocFragment]
                                    ) -> Union[ComparamSpec, ComplexComparamSpec]:
    if et_element.tag == "COMPARAM":
        return ComparamSpec.from_et(et_element, doc_frags)
    elif et_element.tag == "COMPLEX-COMPARAM":
        return ComplexComparamSpec.from_et(et_element, doc_frags)

    raise RuntimeError(f"Unhandled communication parameter type {et_element.tag}")
