# SPDX-License-Identifier: MIT
from typing import List, Optional
from xml.etree import ElementTree

from .companydata import CompanyData
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment


def create_company_datas_from_et(et_element: Optional[ElementTree.Element],
                                 doc_frags: List[OdxDocFragment]) -> NamedItemList[CompanyData]:
    if et_element is None:
        return NamedItemList()

    return NamedItemList([
        CompanyData.from_et(cd_elem, doc_frags) for cd_elem in et_element.iterfind("COMPANY-DATA")
    ],)
