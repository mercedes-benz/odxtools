# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, List
from xml.etree import ElementTree

from .element import IdentifiableElement, NamedElement
from .odxlink import OdxDocFragment
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    pass


@dataclass
class VariableGroup(IdentifiableElement):

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "VariableGroup":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        return VariableGroup(**kwargs)
