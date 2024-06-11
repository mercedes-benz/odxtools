# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .companydocinfo import CompanyDocInfo
from .docrevision import DocRevision
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass
class AdminData:
    language: Optional[str]
    company_doc_infos: List[CompanyDocInfo]
    doc_revisions: List[DocRevision]

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                doc_frags: List[OdxDocFragment]) -> Optional["AdminData"]:

        if et_element is None:
            return None

        language = et_element.findtext("LANGUAGE")

        company_doc_infos = [
            CompanyDocInfo.from_et(cdi_elem, doc_frags)
            for cdi_elem in et_element.iterfind("COMPANY-DOC-INFOS/COMPANY-DOC-INFO")
        ]

        doc_revisions = [
            DocRevision.from_et(dr_elem, doc_frags)
            for dr_elem in et_element.iterfind("DOC-REVISIONS/DOC-REVISION")
        ]

        return AdminData(
            language=language, company_doc_infos=company_doc_infos, doc_revisions=doc_revisions)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        for cdi in self.company_doc_infos:
            result.update(cdi._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for cdi in self.company_doc_infos:
            cdi._resolve_odxlinks(odxlinks)

        for dr in self.doc_revisions:
            dr._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for cdi in self.company_doc_infos:
            cdi._resolve_snrefs(context)

        for dr in self.doc_revisions:
            dr._resolve_snrefs(context)
