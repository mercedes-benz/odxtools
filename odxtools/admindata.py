# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, Optional
from xml.etree import ElementTree

from .companydocinfo import CompanyDocInfo
from .docrevision import DocRevision
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class AdminData:
    language: str | None = None
    company_doc_infos: list[CompanyDocInfo] = field(default_factory=list)
    doc_revisions: list[DocRevision] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element | None,
                context: OdxDocContext) -> Optional["AdminData"]:

        if et_element is None:
            return None

        language = et_element.findtext("LANGUAGE")

        company_doc_infos = [
            CompanyDocInfo.from_et(cdi_elem, context)
            for cdi_elem in et_element.iterfind("COMPANY-DOC-INFOS/COMPANY-DOC-INFO")
        ]

        doc_revisions = [
            DocRevision.from_et(dr_elem, context)
            for dr_elem in et_element.iterfind("DOC-REVISIONS/DOC-REVISION")
        ]

        return AdminData(
            language=language, company_doc_infos=company_doc_infos, doc_revisions=doc_revisions)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result: dict[OdxLinkId, Any] = {}

        for cdi in self.company_doc_infos:
            result.update(cdi._build_odxlinks())

        for dr in self.doc_revisions:
            result.update(dr._build_odxlinks())

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
