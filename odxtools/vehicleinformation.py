# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .ecugroup import EcuGroup
from .element import NamedElement
from .exceptions import odxraise
from .gatewaylogicallink import GatewayLogicalLink
from .globals import xsi
from .infocomponent import InfoComponent
from .logicallink import LogicalLink
from .memberlogicallink import MemberLogicalLink
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .physicalvehiclelink import PhysicalVehicleLink
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict
from .vehicleconnector import VehicleConnector


@dataclass(kw_only=True)
class VehicleInformation(NamedElement):
    info_component_refs: list[OdxLinkRef] = field(default_factory=list)
    vehicle_connectors: NamedItemList[VehicleConnector] = field(default_factory=NamedItemList)
    logical_links: NamedItemList[LogicalLink] = field(default_factory=NamedItemList)
    ecu_groups: NamedItemList[EcuGroup] = field(default_factory=NamedItemList)
    physical_vehicle_links: NamedItemList[PhysicalVehicleLink] = field(
        default_factory=NamedItemList)
    oid: str | None = None

    @property
    def info_components(self) -> NamedItemList[InfoComponent]:
        return self._info_components

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "VehicleInformation":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        info_component_refs = [
            OdxLinkRef.from_et(ic_ref_elem, context)
            for ic_ref_elem in et_element.iterfind("INFO-COMPONENT-REFS/INFO-COMPONENT-REF")
        ]
        vehicle_connectors = NamedItemList([
            VehicleConnector.from_et(vc_elem, context)
            for vc_elem in et_element.iterfind("VEHICLE-CONNECTORS/VEHICLE-CONNECTOR")
        ])
        logical_links: NamedItemList[LogicalLink] = NamedItemList()
        for logical_link_elem in et_element.iterfind("LOGICAL-LINKS/LOGICAL-LINK"):
            logical_link_type_str = logical_link_elem.attrib.get(f"{xsi}type")
            if logical_link_type_str == "GATEWAY-LOGICAL-LINK":
                logical_links.append(GatewayLogicalLink.from_et(logical_link_elem, context))
            elif logical_link_type_str == "MEMBER-LOGICAL-LINK":
                logical_links.append(MemberLogicalLink.from_et(logical_link_elem, context))
            else:
                odxraise(f"Encountered logical link of illegal type {logical_link_type_str}")
                logical_links.append(InfoComponent.from_et(logical_link_elem, context))

        ecu_groups = NamedItemList([
            EcuGroup.from_et(eg_elem, context)
            for eg_elem in et_element.iterfind("ECU-GROUPS/ECU-GROUP")
        ])
        physical_vehicle_links = NamedItemList([
            PhysicalVehicleLink.from_et(pvl_elem, context)
            for pvl_elem in et_element.iterfind("PHYSICAL-VEHICLE-LINKS/PHYSICAL-VEHICLE-LINK")
        ])
        oid = et_element.attrib.get("OID")

        return VehicleInformation(
            info_component_refs=info_component_refs,
            vehicle_connectors=vehicle_connectors,
            logical_links=logical_links,
            ecu_groups=ecu_groups,
            physical_vehicle_links=physical_vehicle_links,
            oid=oid,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for vehicle_connector in self.vehicle_connectors:
            result.update(vehicle_connector._build_odxlinks())
        for logical_link in self.logical_links:
            result.update(logical_link._build_odxlinks())
        for ecu_group in self.ecu_groups:
            result.update(ecu_group._build_odxlinks())
        for logical_link in self.logical_links:
            result.update(logical_link._build_odxlinks())
        for physical_vehicle_link in self.physical_vehicle_links:
            result.update(physical_vehicle_link._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._info_components = NamedItemList(
            [odxlinks.resolve(x, InfoComponent) for x in self.info_component_refs])

        for vehicle_connector in self.vehicle_connectors:
            vehicle_connector._resolve_odxlinks(odxlinks)
        for logical_link in self.logical_links:
            logical_link._resolve_odxlinks(odxlinks)
        for ecu_group in self.ecu_groups:
            ecu_group._resolve_odxlinks(odxlinks)
        for logical_link in self.logical_links:
            logical_link._resolve_odxlinks(odxlinks)
        for physical_vehicle_link in self.physical_vehicle_links:
            physical_vehicle_link._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for vehicle_connector in self.vehicle_connectors:
            vehicle_connector._resolve_snrefs(context)
        for logical_link in self.logical_links:
            logical_link._resolve_snrefs(context)
        for ecu_group in self.ecu_groups:
            ecu_group._resolve_snrefs(context)
        for logical_link in self.logical_links:
            logical_link._resolve_snrefs(context)
        for physical_vehicle_link in self.physical_vehicle_links:
            physical_vehicle_link._resolve_snrefs(context)
