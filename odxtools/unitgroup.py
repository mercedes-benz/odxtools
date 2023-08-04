# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from .exceptions import odxassert
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .unit import Unit
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

UnitGroupCategory = Literal["COUNTRY", "EQUIV-UNITS"]


@dataclass
class UnitGroup:
    """A group of units.

    There are two categories of groups: COUNTRY and EQUIV-UNITS.
    """

    short_name: str
    category: UnitGroupCategory
    unit_refs: List[OdxLinkRef]
    oid: Optional[str]
    long_name: Optional[str]
    description: Optional[str]

    def __post_init__(self):
        self._units = NamedItemList[Unit](short_name_as_id)

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "UnitGroup":
        oid = et_element.get("OID")
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        category = et_element.findtext("CATEGORY")
        odxassert(
            category in ["COUNTRY", "EQUIV-UNITS"],
            f'A UNIT-GROUP-CATEGORY must be "COUNTRY" or "EQUIV-UNITS". It was "{category}".')
        unit_refs = []

        for el in et_element.iterfind("UNIT-REFS/UNIT-REF"):
            ref = OdxLinkRef.from_et(el, doc_frags)
            odxassert(isinstance(ref, OdxLinkRef))
            unit_refs.append(ref)

        return UnitGroup(
            short_name=short_name,
            category=category,
            unit_refs=unit_refs,
            oid=oid,
            long_name=long_name,
            description=description,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._units = NamedItemList[Unit](short_name_as_id,
                                          [odxlinks.resolve(ref) for ref in self.unit_refs])

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def units(self) -> NamedItemList[Unit]:
        return self._units
