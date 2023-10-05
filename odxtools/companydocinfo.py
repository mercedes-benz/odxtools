# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .companydata import CompanyData
from .createsdgs import create_sdgs_from_et
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .specialdatagroup import SpecialDataGroup
from .teammember import TeamMember

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class CompanyDocInfo:
    company_data_ref: OdxLinkRef
    team_member_ref: Optional[OdxLinkRef]
    doc_label: Optional[str]
    sdgs: List[SpecialDataGroup]

    @property
    def company_data(self) -> CompanyData:
        return self._company_data

    @property
    def team_member(self) -> Optional[TeamMember]:
        return self._team_member

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "CompanyDocInfo":
        # the company data reference is mandatory
        company_data_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("COMPANY-DATA-REF"), doc_frags))
        team_member_ref = OdxLinkRef.from_et(et_element.find("TEAM-MEMBER-REF"), doc_frags)
        doc_label = et_element.findtext("DOC-LABEL")
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return CompanyDocInfo(
            company_data_ref=company_data_ref,
            team_member_ref=team_member_ref,
            doc_label=doc_label,
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._company_data = odxlinks.resolve(self.company_data_ref, CompanyData)

        self._team_member: Optional[TeamMember] = None
        if self.team_member_ref is not None:
            self._team_member = odxlinks.resolve(self.team_member_ref, TeamMember)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
