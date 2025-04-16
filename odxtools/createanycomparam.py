from xml.etree import ElementTree

from .comparam import Comparam
from .complexcomparam import ComplexComparam
from .odxdoccontext import OdxDocContext


def create_any_comparam_from_et(et_element: ElementTree.Element,
                                context: OdxDocContext) -> Comparam | ComplexComparam:
    if et_element.tag == "COMPARAM":
        return Comparam.from_et(et_element, context)
    elif et_element.tag == "COMPLEX-COMPARAM":
        return ComplexComparam.from_et(et_element, context)

    raise RuntimeError(f"Unhandled communication parameter type {et_element.tag}")
