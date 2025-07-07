# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .ecuproxy import EcuProxy
from .exceptions import odxraise
from .globals import xsi
from .infocomponent import InfoComponent
from .modelyear import ModelYear
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .oem import Oem
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict
from .vehicleinformation import VehicleInformation
from .vehiclemodel import VehicleModel
from .vehicletype import VehicleType

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class VehicleInfoSpec(OdxCategory):
    info_components: NamedItemList[InfoComponent] = field(default_factory=NamedItemList)
    vehicle_informations: NamedItemList[VehicleInformation] = field(default_factory=NamedItemList)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "VehicleInfoSpec":

        base_obj = OdxCategory.from_et(et_element, context)
        kwargs = dataclass_fields_asdict(base_obj)

        info_components: NamedItemList[InfoComponent] = NamedItemList()
        for info_component_elem in et_element.iterfind("INFO-COMPONENTS/INFO-COMPONENT"):
            info_component_type_str = info_component_elem.attrib.get(f"{xsi}type")
            if info_component_type_str == "ECU-PROXY":
                info_components.append(EcuProxy.from_et(info_component_elem, context))
            elif info_component_type_str == "MODEL-YEAR":
                info_components.append(ModelYear.from_et(info_component_elem, context))
            elif info_component_type_str == "OEM":
                info_components.append(Oem.from_et(info_component_elem, context))
            elif info_component_type_str == "VEHICLE-MODEL":
                info_components.append(VehicleModel.from_et(info_component_elem, context))
            elif info_component_type_str == "VEHICLE-TYPE":
                info_components.append(VehicleType.from_et(info_component_elem, context))
            else:
                odxraise(f"Encountered info component of illegal type {info_component_type_str}")
                info_components.append(InfoComponent.from_et(info_component_elem, context))

        vehicle_informations = NamedItemList([
            VehicleInformation.from_et(el, context)
            for el in et_element.iterfind("VEHICLE-INFORMATIONS/VEHICLE-INFORMATION")
        ])

        return VehicleInfoSpec(
            info_components=info_components, vehicle_informations=vehicle_informations, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for info_component in self.info_components:
            odxlinks.update(info_component._build_odxlinks())
        for vehicle_information in self.vehicle_informations:
            odxlinks.update(vehicle_information._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for info_component in self.info_components:
            info_component._resolve_odxlinks(odxlinks)
        for vehicle_information in self.vehicle_informations:
            vehicle_information._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for info_component in self.info_components:
            info_component._resolve_snrefs(context)
        for vehicle_information in self.vehicle_informations:
            vehicle_information._resolve_snrefs(context)
