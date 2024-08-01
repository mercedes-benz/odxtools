# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .companydata import CompanyData
from .diaglayers.basevariant import BaseVariant
from .diaglayers.diaglayer import DiagLayer
from .diaglayers.ecushareddata import EcuSharedData
from .diaglayers.ecuvariant import EcuVariant
from .diaglayers.functionalgroup import FunctionalGroup
from .diaglayers.protocol import Protocol
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass
class DiagLayerContainer(IdentifiableElement):
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    ecu_shared_datas: NamedItemList[EcuSharedData]
    protocols: NamedItemList[Protocol]
    functional_groups: NamedItemList[FunctionalGroup]
    base_variants: NamedItemList[BaseVariant]
    ecu_variants: NamedItemList[EcuVariant]
    sdgs: List[SpecialDataGroup]

    @property
    def ecus(self) -> NamedItemList[EcuVariant]:
        """ECU variants defined in the container

        This property is an alias for `.ecu_variants`"""
        return self.ecu_variants

    def __post_init__(self) -> None:
        self._diag_layers = NamedItemList[DiagLayer](chain(
            self.ecu_shared_datas,
            self.protocols,
            self.functional_groups,
            self.base_variants,
            self.ecu_variants,
        ),)

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DiagLayerContainer":

        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        # create the current ODX "document fragment" (description of the
        # current document for references and IDs)
        doc_frags = [OdxDocFragment(short_name, "CONTAINER")]
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        company_datas = NamedItemList([
            CompanyData.from_et(cde, doc_frags)
            for cde in et_element.iterfind("COMPANY-DATAS/COMPANY-DATA")
        ])
        ecu_shared_datas = NamedItemList([
            EcuSharedData.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("ECU-SHARED-DATAS/ECU-SHARED-DATA")
        ])
        protocols = NamedItemList([
            Protocol.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("PROTOCOLS/PROTOCOL")
        ])
        functional_groups = NamedItemList([
            FunctionalGroup.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("FUNCTIONAL-GROUPS/FUNCTIONAL-GROUP")
        ])
        base_variants = NamedItemList([
            BaseVariant.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("BASE-VARIANTS/BASE-VARIANT")
        ])
        ecu_variants = NamedItemList([
            EcuVariant.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("ECU-VARIANTS/ECU-VARIANT")
        ])
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        return DiagLayerContainer(
            admin_data=admin_data,
            company_datas=company_datas,
            ecu_shared_datas=ecu_shared_datas,
            protocols=protocols,
            functional_groups=functional_groups,
            base_variants=base_variants,
            ecu_variants=ecu_variants,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())
        for cd in self.company_datas:
            result.update(cd._build_odxlinks())
        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        for ecu_shared_data in self.ecu_shared_datas:
            result.update(ecu_shared_data._build_odxlinks())
        for protocol in self.protocols:
            result.update(protocol._build_odxlinks())
        for functional_group in self.functional_groups:
            result.update(functional_group._build_odxlinks())
        for base_variant in self.base_variants:
            result.update(base_variant._build_odxlinks())
        for ecu_variant in self.ecu_variants:
            result.update(ecu_variant._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)
        for cd in self.company_datas:
            cd._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        for ecu_shared_data in self.ecu_shared_datas:
            ecu_shared_data._resolve_odxlinks(odxlinks)
        for protocol in self.protocols:
            protocol._resolve_odxlinks(odxlinks)
        for functional_group in self.functional_groups:
            functional_group._resolve_odxlinks(odxlinks)
        for base_variant in self.base_variants:
            base_variant._resolve_odxlinks(odxlinks)
        for ecu_variant in self.ecu_variants:
            ecu_variant._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        for ecu_shared_data in self.ecu_shared_datas:
            ecu_shared_data._finalize_init(database, odxlinks)
        for protocol in self.protocols:
            protocol._finalize_init(database, odxlinks)
        for functional_group in self.functional_groups:
            functional_group._finalize_init(database, odxlinks)
        for base_variant in self.base_variants:
            base_variant._finalize_init(database, odxlinks)
        for ecu_variant in self.ecu_variants:
            ecu_variant._finalize_init(database, odxlinks)

    @property
    def diag_layers(self) -> NamedItemList[DiagLayer]:
        return self._diag_layers

    def __getitem__(self, key: Union[int, str]) -> DiagLayer:
        return self.diag_layers[key]
