# SPDX-License-Identifier: MIT
import typing
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, runtime_checkable
from xml.etree import ElementTree

from .element import IdentifiableElement, NamedElement
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    pass


@runtime_checkable
class HasVariableGroups(typing.Protocol):

    @property
    def variable_groups(self) -> NamedItemList["VariableGroup"]:
        ...


@dataclass
class VariableGroup(IdentifiableElement):

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "VariableGroup":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        return VariableGroup(**kwargs)
