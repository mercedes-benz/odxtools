# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict
from .vehicleconnectorpin import VehicleConnectorPin


@dataclass(kw_only=True)
class VehicleConnector(NamedElement):
    vehicle_connector_pins: NamedItemList[VehicleConnectorPin] = field(
        default_factory=NamedItemList)
    oid: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "VehicleConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        vehicle_connector_pins = NamedItemList([
            VehicleConnectorPin.from_et(vc_elem, context)
            for vc_elem in et_element.iterfind("VEHICLE-CONNECTOR-PINS/VEHICLE-CONNECTOR-PIN")
        ])
        oid = et_element.attrib.get("OID")

        return VehicleConnector(vehicle_connector_pins=vehicle_connector_pins, oid=oid, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for vehicle_connector_pin in self.vehicle_connector_pins:
            result.update(vehicle_connector_pin._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for vehicle_connector_pin in self.vehicle_connector_pins:
            vehicle_connector_pin._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for vehicle_connector_pin in self.vehicle_connector_pins:
            vehicle_connector_pin._resolve_snrefs(context)
