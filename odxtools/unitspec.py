# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List
from xml.etree import ElementTree

from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .physicaldimension import PhysicalDimension
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .unit import Unit
from .unitgroup import UnitGroup


@dataclass
class UnitSpec:
    """
    A unit spec encapsulates three lists:

    * unit groups
    * units
    * physical_dimensions

    The following odx elements are not internalized: ADMIN-DATA, SDGS
    """

    # TODO (?): Why are there type errors...
    unit_groups: NamedItemList[UnitGroup]
    units: NamedItemList[Unit]
    physical_dimensions: NamedItemList[PhysicalDimension]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self) -> None:
        self.unit_groups = NamedItemList(self.unit_groups)
        self.units = NamedItemList(self.units)
        self.physical_dimensions = NamedItemList(self.physical_dimensions)

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "UnitSpec":

        unit_groups = NamedItemList([
            UnitGroup.from_et(el, doc_frags) for el in et_element.iterfind("UNIT-GROUPS/UNIT-GROUP")
        ])
        units = NamedItemList(
            [Unit.from_et(el, doc_frags) for el in et_element.iterfind("UNITS/UNIT")])
        physical_dimensions = NamedItemList([
            PhysicalDimension.from_et(el, doc_frags)
            for el in et_element.iterfind("PHYSICAL-DIMENSIONS/PHYSICAL-DIMENSION")
        ])
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        return UnitSpec(
            unit_groups=unit_groups,
            units=units,
            physical_dimensions=physical_dimensions,
            sdgs=sdgs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        for unit in self.units:
            odxlinks.update(unit._build_odxlinks())
        for dim in self.physical_dimensions:
            odxlinks.update(dim._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for unit in self.units:
            unit._resolve_odxlinks(odxlinks)
        for group in self.unit_groups:
            group._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for unit in self.units:
            unit._resolve_snrefs(context)
        for group in self.unit_groups:
            group._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
