# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .admindata import AdminData
from .companydata import CompanyData
from .comparam import Comparam
from .complexcomparam import ComplexComparam
from .createcompanydatas import create_company_datas_from_et
from .createsdgs import create_sdgs_from_et
from .dataobjectproperty import DataObjectProperty
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .specialdatagroup import SpecialDataGroup
from .unitspec import UnitSpec
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class ComparamSubset(IdentifiableElement):
    # mandatory in ODX 2.2, but non existent in ODX 2.0
    category: Optional[str]
    data_object_props: NamedItemList[DataObjectProperty]
    comparams: NamedItemList[Comparam]
    complex_comparams: NamedItemList[ComplexComparam]
    unit_spec: Optional[UnitSpec]
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ComparamSubset":

        category = et_element.get("CATEGORY")

        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        doc_frags = [OdxDocFragment(short_name, str(et_element.tag))]
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        company_datas = create_company_datas_from_et(et_element.find("COMPANY-DATAS"), doc_frags)

        data_object_props = NamedItemList([
            DataObjectProperty.from_et(el, doc_frags)
            for el in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ])
        comparams = NamedItemList(
            [Comparam.from_et(el, doc_frags) for el in et_element.iterfind("COMPARAMS/COMPARAM")])
        complex_comparams = NamedItemList([
            ComplexComparam.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPLEX-COMPARAMS/COMPLEX-COMPARAM")
        ])
        if unit_spec_elem := et_element.find("UNIT-SPEC"):
            unit_spec = UnitSpec.from_et(unit_spec_elem, doc_frags)
        else:
            unit_spec = None

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return ComparamSubset(
            category=category,
            admin_data=admin_data,
            company_datas=company_datas,
            data_object_props=data_object_props,
            comparams=comparams,
            complex_comparams=complex_comparams,
            unit_spec=unit_spec,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        if self.odx_id is not None:
            odxlinks[self.odx_id] = self

        for dop in self.data_object_props:
            odxlinks[dop.odx_id] = dop

        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())

        for ccomparam in self.complex_comparams:
            odxlinks.update(ccomparam._build_odxlinks())

        if self.unit_spec:
            odxlinks.update(self.unit_spec._build_odxlinks())

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())

        if self.company_datas is not None:
            for cd in self.company_datas:
                odxlinks.update(cd._build_odxlinks())

        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for dop in self.data_object_props:
            dop._resolve_odxlinks(odxlinks)

        for comparam in self.comparams:
            comparam._resolve_odxlinks(odxlinks)

        for ccomparam in self.complex_comparams:
            ccomparam._resolve_odxlinks(odxlinks)

        if self.unit_spec:
            self.unit_spec._resolve_odxlinks(odxlinks)

        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for dop in self.data_object_props:
            dop._resolve_snrefs(diag_layer)

        for comparam in self.comparams:
            comparam._resolve_snrefs(diag_layer)

        for ccomparam in self.complex_comparams:
            ccomparam._resolve_snrefs(diag_layer)

        if self.unit_spec:
            self.unit_spec._resolve_snrefs(diag_layer)

        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(diag_layer)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_snrefs(diag_layer)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
