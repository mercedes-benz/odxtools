# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .companydata import CompanyData
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass
class CompanyRevisionInfo:
    company_data_ref: OdxLinkRef
    revision_label: str | None
    state: str | None

    @property
    def company_data(self) -> CompanyData:
        return self._company_data

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: list[OdxDocFragment]) -> "CompanyRevisionInfo":

        company_data_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("COMPANY-DATA-REF"), doc_frags))
        revision_label = et_element.findtext("REVISION-LABEL")
        state = et_element.findtext("STATE")

        return CompanyRevisionInfo(
            company_data_ref=company_data_ref, revision_label=revision_label, state=state)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._company_data = odxlinks.resolve(self.company_data_ref, CompanyData)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
