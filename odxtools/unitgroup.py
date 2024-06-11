# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from .element import NamedElement
from .exceptions import odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .unit import Unit
from .utils import dataclass_fields_asdict


class UnitGroupCategory(Enum):
    COUNTRY = "COUNTRY"
    EQUIV_UNITS = "EQUIV-UNITS"


@dataclass
class UnitGroup(NamedElement):
    """A group of units.

    There are two categories of groups: COUNTRY and EQUIV-UNITS.
    """
    category: UnitGroupCategory
    unit_refs: List[OdxLinkRef]
    oid: Optional[str]

    def __post_init__(self) -> None:
        self._units = NamedItemList[Unit]()

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "UnitGroup":
        oid = et_element.get("OID")
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))
        category_str = odxrequire(et_element.findtext("CATEGORY"))
        try:
            category = UnitGroupCategory(category_str)
        except ValueError:
            category = cast(UnitGroupCategory, None)
            odxraise(f"Encountered unknown unit group category '{category_str}'")

        unit_refs: List[OdxLinkRef] = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("UNIT-REFS/UNIT-REF")
        ]

        return UnitGroup(category=category, unit_refs=unit_refs, oid=oid, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._units = NamedItemList[Unit]([odxlinks.resolve(ref) for ref in self.unit_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass

    @property
    def units(self) -> NamedItemList[Unit]:
        return self._units
