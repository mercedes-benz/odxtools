# SPDX-License-Identifier: MIT

from itertools import chain
from typing import List, Optional, Union

from .admindata import AdminData
from .companydata import CompanyData, create_company_datas_from_et
from .diaglayer import DiagLayer
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .utils import create_description_from_et, short_name_as_id


class DiagLayerContainer:

    def __init__(
        self,
        *,
        odx_id: OdxLinkId,
        short_name: str,
        long_name: Optional[str],
        description: Optional[str],
        admin_data: Optional[AdminData],
        company_datas: Optional[NamedItemList[CompanyData]],
        ecu_shared_datas: List[DiagLayer],
        protocols: List[DiagLayer],
        functional_groups: List[DiagLayer],
        base_variants: List[DiagLayer],
        ecu_variants: List[DiagLayer],
        sdgs: List[SpecialDataGroup],
    ) -> None:
        self.odx_id = odx_id
        self.short_name = short_name
        self.long_name = long_name
        self.description = description
        self.admin_data = admin_data
        self.company_datas = company_datas

        self.ecu_shared_datas = ecu_shared_datas
        self.protocols = protocols
        self.functional_groups = functional_groups
        self.base_variants = base_variants
        self.ecu_variants = ecu_variants
        self.sdgs = sdgs

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
    def from_et(et_element) -> "DiagLayerContainer":
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")

        # create the current ODX "document fragment" (description of the
        # current document for references and IDs)
        doc_frags = [OdxDocFragment(short_name, "CONTAINER")]

        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        description = create_description_from_et(et_element.find("DESC"))
        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        company_datas = create_company_datas_from_et(et_element.find("COMPANY-DATAS"), doc_frags)
        ecu_shared_datas = [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("ECU-SHARED-DATAS/ECU-SHARED-DATA")
        ]
        protocols = [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("PROTOCOLS/PROTOCOL")
        ]
        functional_groups = [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("FUNCTIONAL-GROUPS/FUNCTIONAL-GROUP")
        ]
        base_variants = [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("BASE-VARIANTS/BASE-VARIANT")
        ]
        ecu_variants = [
            DiagLayer.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("ECU-VARIANTS/ECU-VARIANT")
        ]
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

    def __repr__(self) -> str:
        return f"DiagLayerContainer('{self.short_name}')"

    def __str__(self) -> str:
        return f"DiagLayerContainer('{self.short_name}')"
