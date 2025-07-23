# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .linkcomparamref import LinkComparamRef
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict
from .vehicleconnectorpin import VehicleConnectorPin


@dataclass(kw_only=True)
class PhysicalVehicleLink(IdentifiableElement):
    vehicle_connector_pin_refs: list[OdxLinkRef] = field(default_factory=list)
    link_comparam_refs_raw: list[LinkComparamRef] = field(default_factory=list)
    link_type: str

    @property
    def vehicle_connector_pins(self) -> NamedItemList[VehicleConnectorPin]:
        return self._vehicle_connector_pins

    @property
    def link_comparam_refs(self) -> NamedItemList[LinkComparamRef]:
        return self._link_comparam_refs

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "PhysicalVehicleLink":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        vehicle_connector_pin_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("VEHICLE-CONNECTOR-PIN-REFS/VEHICLE-CONNECTOR-PIN-REF")
        ]
        link_comparam_refs_raw = [
            LinkComparamRef.from_et(el, context)
            for el in et_element.iterfind("LINK-COMPARAM-REFS/LINK-COMPARAM-REF")
        ]
        link_type = odxrequire(et_element.attrib.get("TYPE"))

        return PhysicalVehicleLink(
            vehicle_connector_pin_refs=vehicle_connector_pin_refs,
            link_comparam_refs_raw=link_comparam_refs_raw,
            link_type=link_type,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for link_comparam_ref in self.link_comparam_refs_raw:
            odxlinks.update(link_comparam_ref._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._vehicle_connector_pins = NamedItemList(
            [odxlinks.resolve(x, VehicleConnectorPin) for x in self.vehicle_connector_pin_refs])

        for link_comparam_ref in self.link_comparam_refs_raw:
            link_comparam_ref._resolve_odxlinks(odxlinks)

        self._link_comparam_refs = NamedItemList(self.link_comparam_refs_raw)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for link_comparam_ref in self.link_comparam_refs_raw:
            link_comparam_ref._resolve_snrefs(context)
