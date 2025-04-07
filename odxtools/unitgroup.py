# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, cast
from xml.etree import ElementTree

from .element import NamedElement
from .exceptions import odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .unit import Unit
from .unitgroupcategory import UnitGroupCategory
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class UnitGroup(NamedElement):
    """A group of units.

    There are two categories of groups: COUNTRY and EQUIV-UNITS.
    """
    category: UnitGroupCategory
    unit_refs: list[OdxLinkRef] = field(default_factory=list)
    oid: str | None = None

    @property
    def units(self) -> NamedItemList[Unit]:
        return self._units

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "UnitGroup":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        category_str = odxrequire(et_element.findtext("CATEGORY"))
        try:
            category = UnitGroupCategory(category_str)
        except ValueError:
            category = cast(UnitGroupCategory, None)
            odxraise(f"Encountered unknown unit group category '{category_str}'")

        unit_refs = [
            odxrequire(OdxLinkRef.from_et(el, context))
            for el in et_element.iterfind("UNIT-REFS/UNIT-REF")
        ]
        oid = et_element.get("OID")

        return UnitGroup(category=category, unit_refs=unit_refs, oid=oid, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._units = NamedItemList[Unit]([odxlinks.resolve(ref) for ref in self.unit_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
