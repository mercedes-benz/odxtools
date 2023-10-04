# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union
from xml.etree import ElementTree

from .createsdgs import create_sdgs_from_et
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .physicaldimension import PhysicalDimension
from .specialdatagroup import SpecialDataGroup
from .unit import Unit
from .unitgroup import UnitGroup

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


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
    unit_groups: Union[NamedItemList[UnitGroup], List[UnitGroup]]
    units: Union[NamedItemList[Unit], List[Unit]]
    physical_dimensions: Union[NamedItemList[PhysicalDimension], List[PhysicalDimension]]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self) -> None:
        self.unit_groups = NamedItemList(self.unit_groups)
        self.units = NamedItemList(self.units)
        self.physical_dimensions = NamedItemList(self.physical_dimensions)

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "UnitSpec":

        unit_groups = [
            UnitGroup.from_et(el, doc_frags) for el in et_element.iterfind("UNIT-GROUPS/UNIT-GROUP")
        ]
        units = [Unit.from_et(el, doc_frags) for el in et_element.iterfind("UNITS/UNIT")]
        physical_dimensions = [
            PhysicalDimension.from_et(el, doc_frags)
            for el in et_element.iterfind("PHYSICAL-DIMENSIONS/PHYSICAL-DIMENSION")
        ]
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

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

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for unit in self.units:
            unit._resolve_snrefs(diag_layer)
        for group in self.unit_groups:
            group._resolve_snrefs(diag_layer)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
