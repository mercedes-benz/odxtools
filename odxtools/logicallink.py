# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, cast
from xml.etree import ElementTree

from .diaglayers.basevariant import BaseVariant
from .diaglayers.functionalgroup import FunctionalGroup
from .diaglayers.protocol import Protocol
from .ecuproxy import EcuProxy
from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .globals import xsi
from .linkcomparamref import LinkComparamRef
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .physicalvehiclelink import PhysicalVehicleLink
from .protstack import ProtStack
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .gatewaylogicallink import GatewayLogicalLink


class LogicalLinkType(Enum):
    GATEWAY_LOGICAL_LINK = "GATEWAY-LOGICAL-LINK"
    MEMBER_LOGICAL_LINK = "MEMBER-LOGICAL-LINK"


@dataclass(kw_only=True)
class LogicalLink(IdentifiableElement):
    link_type: LogicalLinkType
    gateway_logical_link_refs: list[OdxLinkRef] = field(default_factory=list)
    physical_vehicle_link_ref: OdxLinkRef
    protocol_ref: OdxLinkRef | None = None
    functional_group_ref: OdxLinkRef | None = None
    base_variant_ref: OdxLinkRef | None = None
    ecu_proxy_refs: list[OdxLinkRef] = field(default_factory=list)
    link_comparam_refs_raw: list[LinkComparamRef] = field(default_factory=list)
    prot_stack_snref: str | None = None

    @property
    def gateway_logical_links(self) -> NamedItemList["GatewayLogicalLink"]:
        return self._gateway_logical_links

    @property
    def physical_vehicle_link(self) -> PhysicalVehicleLink:
        return self._physical_vehicle_link

    @property
    def protocol(self) -> Protocol | None:
        return self._protocol

    @property
    def functional_group(self) -> FunctionalGroup | None:
        return self._functional_group

    @property
    def base_variant(self) -> BaseVariant | None:
        return self._base_variant

    @property
    def ecu_proxies(self) -> NamedItemList[EcuProxy]:
        return self._ecu_proxies

    @property
    def link_comparam_refs(self) -> NamedItemList[LinkComparamRef]:
        return self._link_comparam_refs

    @property
    def prot_stack(self) -> ProtStack | None:
        return self._prot_stack

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "LogicalLink":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        link_type_str = odxrequire(et_element.attrib.get(f"{xsi}type"))
        try:
            link_type = LogicalLinkType(link_type_str)
        except ValueError:
            odxraise(f"Encountered unknown LOGICAL-LINK type '{link_type_str}'")
            link_type = cast(LogicalLinkType, None)

        gateway_logical_link_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("GATEWAY-LOGICAL-LINK-REFS/GATEWAY-LOGICAL-LINK-REF")
        ]

        physical_vehicle_link_ref = OdxLinkRef.from_et(
            odxrequire(et_element.find("PHYSICAL-VEHICLE-LINK-REF")), context)
        protocol_ref = OdxLinkRef.from_et(et_element.find("PROTOCOL-REF"), context)
        functional_group_ref = OdxLinkRef.from_et(et_element.find("FUNCTIONAL-GROUP-REF"), context)
        base_variant_ref = OdxLinkRef.from_et(et_element.find("BASE-VARIANT-REF"), context)
        ecu_proxy_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("ECU-PROXY-REFS/ECU-PROXY-REF")
        ]
        link_comparam_refs_raw = [
            LinkComparamRef.from_et(el, context)
            for el in et_element.iterfind("LINK-COMPARAM-REFS/LINK-COMPARAM-REF")
        ]
        prot_stack_snref = None
        if (prot_stack_snref_elem := et_element.find("PROT-STACK-SNREF")) is not None:
            prot_stack_snref = odxrequire(prot_stack_snref_elem.attrib.get("SHORT-NAME"))

        return LogicalLink(
            link_type=link_type,
            gateway_logical_link_refs=gateway_logical_link_refs,
            physical_vehicle_link_ref=physical_vehicle_link_ref,
            protocol_ref=protocol_ref,
            functional_group_ref=functional_group_ref,
            base_variant_ref=base_variant_ref,
            ecu_proxy_refs=ecu_proxy_refs,
            link_comparam_refs_raw=link_comparam_refs_raw,
            prot_stack_snref=prot_stack_snref,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for lcp_ref in self.link_comparam_refs_raw:
            result.update(lcp_ref._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for lcp_ref in self.link_comparam_refs_raw:
            lcp_ref._resolve_odxlinks(odxlinks)

        # we can only create a NamedItemList here because the
        # '.short_name' attribute of LinkedComparamRef objects is only
        # defined after ODXLINK resolution...
        self._link_comparam_refs = NamedItemList(self.link_comparam_refs_raw)

        if TYPE_CHECKING:
            self._gateway_logical_links = NamedItemList(
                [odxlinks.resolve(x, GatewayLogicalLink) for x in self.gateway_logical_link_refs])
        else:
            self._gateway_logical_links = NamedItemList(
                [odxlinks.resolve(x) for x in self.gateway_logical_link_refs])

        self._physical_vehicle_link = odxlinks.resolve(self.physical_vehicle_link_ref,
                                                       PhysicalVehicleLink)

        self._protocol = None
        if self.protocol_ref is not None:
            self._protocol = odxlinks.resolve(self.protocol_ref, Protocol)

        self._functional_group = None
        if self.functional_group_ref is not None:
            self._functional_group = odxlinks.resolve(self.functional_group_ref, FunctionalGroup)

        self._base_variant = None
        if self.base_variant_ref is not None:
            self._base_variant = odxlinks.resolve(self.base_variant_ref, BaseVariant)

        self._ecu_proxies = NamedItemList(
            [odxlinks.resolve(x, EcuProxy) for x in self.ecu_proxy_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for lcp_ref in self.link_comparam_refs_raw:
            lcp_ref._resolve_snrefs(context)

        self._prot_stack = None
        # TODO: resolve prot_stack_snref
        # if self.prot_stack_snref is not None:
        #    self._prot_stack = resolve_snref(self.prot_stack_snref, context., ProtStack, use_weakrefs=context.use_weakrefs)
