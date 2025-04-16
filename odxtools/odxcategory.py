# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .admindata import AdminData
from .companydata import CompanyData
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class OdxCategory(IdentifiableElement):
    """This is the base class for all top-level container classes in ODX"""

    admin_data: AdminData | None = None
    company_datas: NamedItemList[CompanyData] = field(default_factory=NamedItemList)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "OdxCategory":
        raise Exception("Calling `._from_et()` is not allowed for OdxCategory. "
                        "Use `OdxCategory.category_from_et()`!")

    @staticmethod
    def category_from_et(et_element: ElementTree.Element, context: OdxDocContext, *,
                         doc_type: DocType) -> "OdxCategory":

        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        # create the current ODX "document fragment" (description of the
        # current document for references and IDs)
        context.doc_fragments.append(OdxDocFragment(short_name, doc_type))
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        company_datas = NamedItemList([
            CompanyData.from_et(cde, context)
            for cde in et_element.iterfind("COMPANY-DATAS/COMPANY-DATA")
        ])
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return OdxCategory(admin_data=admin_data, company_datas=company_datas, sdgs=sdgs, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())
        for cd in self.company_datas:
            result.update(cd._build_odxlinks())
        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)
        for cd in self.company_datas:
            cd._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)
        for cd in self.company_datas:
            cd._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
