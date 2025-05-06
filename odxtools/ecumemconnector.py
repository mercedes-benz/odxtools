# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .diaglayers.basevariant import BaseVariant
from .diaglayers.ecuvariant import EcuVariant
from .ecumem import EcuMem
from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .flashclass import FlashClass
from .identdesc import IdentDesc
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .sessiondesc import SessionDesc
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class EcuMemConnector(IdentifiableElement):
    admin_data: AdminData | None = None
    flash_classes: NamedItemList[FlashClass]
    session_descs: NamedItemList[SessionDesc] = field(default_factory=NamedItemList)
    ident_descs: list[IdentDesc] = field(default_factory=list)
    ecu_mem_ref: OdxLinkRef
    layer_refs: list[OdxLinkRef]
    all_variant_refs: list[OdxLinkRef]
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @property
    def ecu_mem(self) -> EcuMem:
        return self._ecu_mem

    @property
    def layers(self) -> NamedItemList[EcuVariant | BaseVariant]:
        return self._layers

    @property
    def all_variants(self) -> NamedItemList[BaseVariant]:
        return self._all_variants

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuMemConnector":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        flash_classes = NamedItemList([
            FlashClass.from_et(el, context)
            for el in et_element.iterfind("FLASH-CLASSS/FLASH-CLASS")
        ])
        session_descs = NamedItemList([
            SessionDesc.from_et(el, context)
            for el in et_element.iterfind("SESSION-DESCS/SESSION-DESC")
        ])
        ident_descs = [
            IdentDesc.from_et(el, context) for el in et_element.iterfind("IDENT-DESCS/IDENT-DESC")
        ]
        ecu_mem_ref = OdxLinkRef.from_et(odxrequire(et_element.find("ECU-MEM-REF")), context)
        layer_refs = [
            OdxLinkRef.from_et(el, context) for el in et_element.iterfind("LAYER-REFS/LAYER-REF")
        ]
        all_variant_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("ALL-VARIANT-REFS/ALL-VARIANT-REF")
        ]
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return EcuMemConnector(
            admin_data=admin_data,
            flash_classes=flash_classes,
            session_descs=session_descs,
            ident_descs=ident_descs,
            ecu_mem_ref=ecu_mem_ref,
            layer_refs=layer_refs,
            all_variant_refs=all_variant_refs,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())
        for flash_class in self.flash_classes:
            odxlinks.update(flash_class._build_odxlinks())
        for session_desc in self.session_descs:
            odxlinks.update(session_desc._build_odxlinks())
        for ident_desc in self.ident_descs:
            odxlinks.update(ident_desc._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._ecu_mem = odxlinks.resolve(self.ecu_mem_ref, EcuMem)

        tmp = []
        for ref in self.layer_refs:
            x = odxlinks.resolve(ref)
            if not isinstance(x, (BaseVariant, EcuVariant)):
                odxraise("Invalid type of referenced object")
            tmp.append(x)
        self._layers = NamedItemList(tmp)

        self._all_variants = NamedItemList(
            [odxlinks.resolve(ref, BaseVariant) for ref in self.all_variant_refs])
        self._ecu_mem = odxlinks.resolve(self.ecu_mem_ref, EcuMem)

        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)
        for flash_class in self.flash_classes:
            flash_class._resolve_odxlinks(odxlinks)
        for session_desc in self.session_descs:
            session_desc._resolve_odxlinks(odxlinks)
        for ident_desc in self.ident_descs:
            ident_desc._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)
        for flash_class in self.flash_classes:
            flash_class._resolve_snrefs(context)
        for session_desc in self.session_descs:
            session_desc._resolve_snrefs(context)
        for ident_desc in self.ident_descs:
            ident_desc._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
