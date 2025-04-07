# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .physicaldimension import PhysicalDimension
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .unit import Unit
from .unitgroup import UnitGroup


@dataclass(kw_only=True)
class UnitSpec:
    """
    A unit spec encapsulates three lists:

    * unit groups
    * units
    * physical_dimensions

    The following odx elements are not internalized: ADMIN-DATA, SDGS
    """

    admin_data: AdminData | None = None
    unit_groups: NamedItemList[UnitGroup] = field(default_factory=NamedItemList)
    units: NamedItemList[Unit] = field(default_factory=NamedItemList)
    physical_dimensions: NamedItemList[PhysicalDimension] = field(default_factory=NamedItemList)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.unit_groups = NamedItemList(self.unit_groups)
        self.units = NamedItemList(self.units)
        self.physical_dimensions = NamedItemList(self.physical_dimensions)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "UnitSpec":

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        unit_groups = NamedItemList([
            UnitGroup.from_et(el, context) for el in et_element.iterfind("UNIT-GROUPS/UNIT-GROUP")
        ])
        units = NamedItemList(
            [Unit.from_et(el, context) for el in et_element.iterfind("UNITS/UNIT")])
        physical_dimensions = NamedItemList([
            PhysicalDimension.from_et(el, context)
            for el in et_element.iterfind("PHYSICAL-DIMENSIONS/PHYSICAL-DIMENSION")
        ])
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return UnitSpec(
            admin_data=admin_data,
            unit_groups=unit_groups,
            units=units,
            physical_dimensions=physical_dimensions,
            sdgs=sdgs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}
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
