# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .admindata import AdminData
from .companydata import CompanyData
from .createcompanydatas import create_company_datas_from_et
from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .protstack import ProtStack
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class ComparamSpec(IdentifiableElement):
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    sdgs: List[SpecialDataGroup]
    prot_stacks: NamedItemList[ProtStack]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "ComparamSpec":

        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        doc_frags = [OdxDocFragment(short_name, str(et_element.tag))]
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        company_datas = create_company_datas_from_et(et_element.find("COMPANY-DATAS"), doc_frags)
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        prot_stacks = NamedItemList([
            ProtStack.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("PROT-STACKS/PROT-STACK")
        ])

        return ComparamSpec(
            admin_data=admin_data,
            company_datas=company_datas,
            sdgs=sdgs,
            prot_stacks=prot_stacks,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        if self.odx_id is not None:
            odxlinks[self.odx_id] = self

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())

        for cd in self.company_datas:
            odxlinks.update(cd._build_odxlinks())

        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        for ps in self.prot_stacks:
            odxlinks.update(ps._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        for cd in self.company_datas:
            cd._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        for ps in self.prot_stacks:
            ps._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(diag_layer)

        for cd in self.company_datas:
            cd._resolve_snrefs(diag_layer)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

        for ps in self.prot_stacks:
            ps._resolve_snrefs(diag_layer)
