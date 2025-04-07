# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .companydata import CompanyData
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .teammember import TeamMember


@dataclass(kw_only=True)
class CompanyDocInfo:
    company_data_ref: OdxLinkRef
    team_member_ref: OdxLinkRef | None = None
    doc_label: str | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @property
    def company_data(self) -> CompanyData:
        return self._company_data

    @property
    def team_member(self) -> TeamMember | None:
        return self._team_member

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "CompanyDocInfo":
        # the company data reference is mandatory
        company_data_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("COMPANY-DATA-REF"), context))
        team_member_ref = OdxLinkRef.from_et(et_element.find("TEAM-MEMBER-REF"), context)
        doc_label = et_element.findtext("DOC-LABEL")
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return CompanyDocInfo(
            company_data_ref=company_data_ref,
            team_member_ref=team_member_ref,
            doc_label=doc_label,
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._company_data = odxlinks.resolve(self.company_data_ref, CompanyData)

        self._team_member: TeamMember | None = None
        if self.team_member_ref is not None:
            self._team_member = odxlinks.resolve(self.team_member_ref, TeamMember)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
