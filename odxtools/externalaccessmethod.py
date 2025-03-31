# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment
from .utils import dataclass_fields_asdict


@dataclass
class ExternalAccessMethod(IdentifiableElement):
    method: str

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ExternalAccessMethod":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        method = odxrequire(et_element.findtext("METHOD"))

        return ExternalAccessMethod(method=method, **kwargs)
