# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from itertools import chain
from typing import List, Optional, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .companydata import CompanyData
from .createcompanydatas import create_company_datas_from_et
from .createsdgs import create_sdgs_from_et
from .diaglayer import DiagLayer
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .specialdatagroup import SpecialDataGroup
from .utils import create_description_from_et, short_name_as_id


@dataclass
class DiagLayerContainer:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    ecu_shared_datas: NamedItemList[DiagLayer]
    protocols: NamedItemList[DiagLayer]
    functional_groups: NamedItemList[DiagLayer]
    base_variants: NamedItemList[DiagLayer]
    ecu_variants: NamedItemList[DiagLayer]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self) -> None:
        self._diag_layers = NamedItemList[DiagLayer](
            short_name_as_id,
            chain(
                self.ecu_shared_datas,
                self.protocols,
                self.functional_groups,
                self.base_variants,
                self.ecu_variants,
            ),
        )

    @staticmethod
    def from_et(et_element: ElementTree.Element) -> "DiagLayerContainer":
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")

        # create the current ODX "document fragment" (description of the
        # current document for references and IDs)
        doc_frags = [OdxDocFragment(short_name, "CONTAINER")]

        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        description = create_description_from_et(et_element.find("DESC"))
        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        company_datas = create_company_datas_from_et(et_element.find("COMPANY-DATAS"), doc_frags)
        ecu_shared_datas = NamedItemList(short_name_as_id, [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("ECU-SHARED-DATAS/ECU-SHARED-DATA")
        ])
        protocols = NamedItemList(short_name_as_id, [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("PROTOCOLS/PROTOCOL")
        ])
        functional_groups = NamedItemList(short_name_as_id, [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("FUNCTIONAL-GROUPS/FUNCTIONAL-GROUP")
        ])
        base_variants = NamedItemList(short_name_as_id, [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("BASE-VARIANTS/BASE-VARIANT")
        ])
        ecu_variants = NamedItemList(short_name_as_id, [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("ECU-VARIANTS/ECU-VARIANT")
        ])
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return DiagLayerContainer(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            admin_data=admin_data,
            company_datas=company_datas,
            ecu_shared_datas=ecu_shared_datas,
            protocols=protocols,
            functional_groups=functional_groups,
            base_variants=base_variants,
            ecu_variants=ecu_variants,
            sdgs=sdgs,
        )

    def _build_odxlinks(self):
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        if self.company_datas is not None:
            for cd in self.company_datas:
                result.update(cd._build_odxlinks())

        for dl in chain(
                self.ecu_shared_datas,
                self.protocols,
                self.functional_groups,
                self.base_variants,
                self.ecu_variants,
        ):
            result.update(dl._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_odxlinks(odxlinks)

        for dl in chain(
                self.ecu_shared_datas,
                self.protocols,
                self.functional_groups,
                self.base_variants,
                self.ecu_variants,
        ):
            dl._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _finalize_init(self, odxlinks: OdxLinkDatabase) -> None:
        for dl in chain(
                self.ecu_shared_datas,
                self.protocols,
                self.functional_groups,
                self.base_variants,
                self.ecu_variants,
        ):
            dl._finalize_init(odxlinks)

    @property
    def diag_layers(self):
        return self._diag_layers

    def __getitem__(self, key: Union[int, str]) -> DiagLayer:
        return self.diag_layers[key]
