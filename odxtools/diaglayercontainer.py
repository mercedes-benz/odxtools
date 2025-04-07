# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .diaglayers.basevariant import BaseVariant
from .diaglayers.diaglayer import DiagLayer
from .diaglayers.ecushareddata import EcuSharedData
from .diaglayers.ecuvariant import EcuVariant
from .diaglayers.functionalgroup import FunctionalGroup
from .diaglayers.protocol import Protocol
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import DocType, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class DiagLayerContainer(OdxCategory):
    protocols: NamedItemList[Protocol] = field(default_factory=NamedItemList)
    functional_groups: NamedItemList[FunctionalGroup] = field(default_factory=NamedItemList)
    ecu_shared_datas: NamedItemList[EcuSharedData] = field(default_factory=NamedItemList)
    base_variants: NamedItemList[BaseVariant] = field(default_factory=NamedItemList)
    ecu_variants: NamedItemList[EcuVariant] = field(default_factory=NamedItemList)

    @property
    def diag_layers(self) -> NamedItemList[DiagLayer]:
        return self._diag_layers

    @property
    def ecus(self) -> NamedItemList[EcuVariant]:
        """ECU variants defined in the container

        This property is an alias for `.ecu_variants`"""
        return self.ecu_variants

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DiagLayerContainer":

        cat = OdxCategory.category_from_et(et_element, context, doc_type=DocType.CONTAINER)
        kwargs = dataclass_fields_asdict(cat)

        protocols = NamedItemList([
            Protocol.from_et(dl_element, context)
            for dl_element in et_element.iterfind("PROTOCOLS/PROTOCOL")
        ])
        functional_groups = NamedItemList([
            FunctionalGroup.from_et(dl_element, context)
            for dl_element in et_element.iterfind("FUNCTIONAL-GROUPS/FUNCTIONAL-GROUP")
        ])
        ecu_shared_datas = NamedItemList([
            EcuSharedData.from_et(dl_element, context)
            for dl_element in et_element.iterfind("ECU-SHARED-DATAS/ECU-SHARED-DATA")
        ])
        base_variants = NamedItemList([
            BaseVariant.from_et(dl_element, context)
            for dl_element in et_element.iterfind("BASE-VARIANTS/BASE-VARIANT")
        ])
        ecu_variants = NamedItemList([
            EcuVariant.from_et(dl_element, context)
            for dl_element in et_element.iterfind("ECU-VARIANTS/ECU-VARIANT")
        ])

        return DiagLayerContainer(
            protocols=protocols,
            functional_groups=functional_groups,
            ecu_shared_datas=ecu_shared_datas,
            base_variants=base_variants,
            ecu_variants=ecu_variants,
            **kwargs)

    def __post_init__(self) -> None:
        self._diag_layers = NamedItemList[DiagLayer](chain(
            self.protocols,
            self.functional_groups,
            self.ecu_shared_datas,
            self.base_variants,
            self.ecu_variants,
        ),)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for protocol in self.protocols:
            result.update(protocol._build_odxlinks())
        for functional_group in self.functional_groups:
            result.update(functional_group._build_odxlinks())
        for ecu_shared_data in self.ecu_shared_datas:
            result.update(ecu_shared_data._build_odxlinks())
        for base_variant in self.base_variants:
            result.update(base_variant._build_odxlinks())
        for ecu_variant in self.ecu_variants:
            result.update(ecu_variant._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for protocol in self.protocols:
            protocol._resolve_odxlinks(odxlinks)
        for functional_group in self.functional_groups:
            functional_group._resolve_odxlinks(odxlinks)
        for ecu_shared_data in self.ecu_shared_datas:
            ecu_shared_data._resolve_odxlinks(odxlinks)
        for base_variant in self.base_variants:
            base_variant._resolve_odxlinks(odxlinks)
        for ecu_variant in self.ecu_variants:
            ecu_variant._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

        for protocol in self.protocols:
            protocol._finalize_init(database, odxlinks)
        for functional_group in self.functional_groups:
            functional_group._finalize_init(database, odxlinks)
        for ecu_shared_data in self.ecu_shared_datas:
            ecu_shared_data._finalize_init(database, odxlinks)
        for base_variant in self.base_variants:
            base_variant._finalize_init(database, odxlinks)
        for ecu_variant in self.ecu_variants:
            ecu_variant._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

    def __getitem__(self, key: int | str) -> DiagLayer:
        return self.diag_layers[key]
