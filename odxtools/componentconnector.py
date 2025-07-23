# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .diaglayers.basevariant import BaseVariant
from .diaglayers.ecuvariant import EcuVariant
from .diagobjectconnector import DiagObjectConnector
from .exceptions import odxraise
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class ComponentConnector:
    ecu_variant_refs: list[OdxLinkRef] = field(default_factory=list)
    base_variant_ref: OdxLinkRef | None = None

    diag_object_connector: DiagObjectConnector | None = None
    diag_object_connector_ref: OdxLinkRef | None = None

    @property
    def ecu_variants(self) -> NamedItemList[EcuVariant]:
        return self._ecu_variants

    @property
    def base_variant(self) -> BaseVariant | None:
        return self._base_variant

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ComponentConnector":
        ecu_variant_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("ECU-VARIANT-REFS/ECU-VARIANT-REF")
        ]
        base_variant_ref = OdxLinkRef.from_et(et_element.find("BASE-VARIANT-REF"), context)
        diag_object_connector = None
        if (doc_elem := et_element.find("DIAG-OBJECT-CONNECTOR")) is not None:
            diag_object_connector = DiagObjectConnector.from_et(doc_elem, context)
        diag_object_connector_ref = OdxLinkRef.from_et(
            et_element.find("DIAG-OBJECT-CONNECTOR-REF"), context)

        return ComponentConnector(
            ecu_variant_refs=ecu_variant_refs,
            base_variant_ref=base_variant_ref,
            diag_object_connector=diag_object_connector,
            diag_object_connector_ref=diag_object_connector_ref)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        if self.diag_object_connector_ref is None:
            if self.diag_object_connector is None:
                odxraise()
            else:
                result.update(self.diag_object_connector._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._ecu_variants = NamedItemList(
            [odxlinks.resolve(ev_ref, EcuVariant) for ev_ref in self.ecu_variant_refs])

        self._base_variant = None
        if self.base_variant_ref is not None:
            self._base_variant = odxlinks.resolve(self.base_variant_ref, BaseVariant)

        if self.diag_object_connector_ref is None:
            if self.diag_object_connector is None:
                odxraise()
            self.diag_object_connector._resolve_odxlinks(odxlinks)
        else:
            self.diag_object_connector = odxlinks.resolve(self.diag_object_connector_ref,
                                                          DiagObjectConnector)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.diag_object_connector_ref is None:
            if self.diag_object_connector is None:
                odxraise()
                return

            self.diag_object_connector._resolve_snrefs(context)
