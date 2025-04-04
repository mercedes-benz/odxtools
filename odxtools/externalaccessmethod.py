# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ExternalAccessMethod(IdentifiableElement):
    method: str

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ExternalAccessMethod":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        method = odxrequire(et_element.findtext("METHOD"))

        return ExternalAccessMethod(method=method, **kwargs)
