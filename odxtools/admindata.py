# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .nameditemlist import NamedItemList
from .companydata import CompanyData, TeamMember
from .odxlink import OdxLinkId, OdxLinkRef, OdxLinkDatabase, OdxDocFragment
from .utils import read_description_from_odx

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

@dataclass()
class CompanyDocInfo:
    company_data_ref: OdxLinkRef
    company_data: Optional[CompanyData] = None
    team_member_ref: Optional[OdxLinkRef] = None
    team_member: Optional[TeamMember] = None
    doc_label: Optional[str] = None

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self.company_data = odxlinks.resolve(self.company_data_ref)

        if self.team_member_ref is not None:
            self.team_member = odxlinks.resolve(self.team_member_ref)

@dataclass()
class Modification:
    change: Optional[str] = None
    reason: Optional[str] = None

@dataclass()
class DocRevision:
    """
    Representation of a single revision of the relevant object.
    """
    date: str
    team_member_ref: Optional[OdxLinkRef] = None
    team_member: Optional[TeamMember] = None
    revision_label: Optional[str] = None
    state: Optional[str] = None
    tool: Optional[str] = None
    modifications: List[Modification] = field(default_factory=list)

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        if self.team_member_ref is not None:
            self.team_member = odxlinks.resolve(self.team_member_ref)

@dataclass()
class AdminData:
    language: Optional[str] = None
    company_doc_infos: Optional[List[CompanyDocInfo]] = None
    doc_revisions: Optional[List[DocRevision]] = None

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        if self.company_doc_infos is not None:
            for cdi in self.company_doc_infos:
                cdi._resolve_references(odxlinks)

        if self.doc_revisions is not None:
            for dr in self.doc_revisions:
                dr._resolve_references(odxlinks)

def read_admin_data_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    if et_element is None:
        return None

    language = et_element.find("LANGUAGE")
    if language is not None:
        language = language.text

    company_doc_infos = et_element.find("COMPANY-DOC-INFOS")
    if company_doc_infos is not None:
        cdilist = list()
        for cdi in company_doc_infos.iterfind("COMPANY-DOC-INFO"):
            # the company data reference is mandatory
            company_data_ref = OdxLinkRef.from_et(cdi.find("COMPANY-DATA-REF"), doc_frags)
            assert company_data_ref is not None
            team_member_ref = OdxLinkRef.from_et(cdi.find("TEAM-MEMBER-REF"), doc_frags)
            assert team_member_ref is not None

            doc_label = cdi.findtext("DOC-LABEL")

            cdilist.append(CompanyDocInfo(company_data_ref=company_data_ref,
                                          team_member_ref=team_member_ref,
                                          doc_label=doc_label))

        company_doc_infos = cdilist

    doc_revisions = et_element.find("DOC-REVISIONS")
    if doc_revisions is not None:
        drlist = list()
        for dr in doc_revisions.iterfind("DOC-REVISION"):
            team_member_ref = OdxLinkRef.from_et(dr.find("TEAM-MEMBER-REF"), doc_frags)
            revision_label = dr.find("REVISION-LABEL")
            if revision_label is not None:
                revision_label = revision_label.text

            state = dr.find("STATE")
            if state is not None:
                state = state.text

            date = dr.find("DATE").text

            tool = dr.find("TOOL")
            if tool is not None:
                tool = tool.text

            modlist = None
            mods = dr.find("MODIFICATIONS")
            if mods is not None:
                modlist = list()
                for mod in mods.iterfind("MODIFICATION"):
                    m_change = mod.find("CHANGE")
                    if m_change is not None:
                        m_change = m_change.text

                    m_reason = mod.find("REASON")
                    if m_reason is not None:
                        m_reason = m_reason.text

                    modlist.append(Modification(change=m_change,
                                                reason=m_reason))

            drlist.append(DocRevision(team_member_ref=team_member_ref,
                                      revision_label=revision_label,
                                      state=state,
                                      date=date,
                                      tool=tool,
                                      modifications=modlist))


        doc_revisions = drlist

    else:
        doc_revisions = []

    return AdminData(language=language,
                     company_doc_infos=company_doc_infos,
                     doc_revisions=doc_revisions)
