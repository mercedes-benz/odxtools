# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .companydata import CompanyData, TeamMember

from dataclasses import dataclass, field
from typing import Optional, List

@dataclass()
class CompanyDocInfo:
    company_data_ref: str
    company_data: Optional[CompanyData] = None
    team_member_ref: Optional[str] = None
    team_member: Optional[TeamMember] = None
    doc_label: Optional[str] = None

    def _resolve_references(self, id_lookup):
        self.company_data = id_lookup[self.company_data_ref]

        if self.team_member_ref is not None:
            self.team_member = id_lookup[self.team_member_ref]

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
    team_member_ref: Optional[str] = None
    team_member: Optional[TeamMember] = None
    revision_label: Optional[str] = None
    state: Optional[str] = None
    tool: Optional[str] = None
    modifications: List[Modification] = field(default_factory=list)

    def _resolve_references(self, id_lookup):
        if self.team_member_ref is not None:
            self.team_member = id_lookup[self.team_member_ref]

@dataclass()
class AdminData:
    language: Optional[str] = None
    company_doc_infos: Optional[List[CompanyDocInfo]] = None
    doc_revisions: Optional[List[DocRevision]] = None

    def _build_id_lookup(self):
        result = {}

        return result

    def _resolve_references(self, id_lookup):
        if self.company_doc_infos is not None:
            for cdi in self.company_doc_infos:
                cdi._resolve_references(id_lookup)

        if self.doc_revisions is not None:
            for dr in self.doc_revisions:
                dr._resolve_references(id_lookup)

def read_admin_data_from_odx(et_element):
    if et_element is None:
        return None

    language = et_element.findtext("LANGUAGE")

    company_doc_infos = et_element.find("COMPANY-DOC-INFOS")
    if company_doc_infos is not None:
        cdilist = list()
        for cdi in company_doc_infos.iterfind("COMPANY-DOC-INFO"):
            # the company data reference is mandatory
            company_data_ref = cdi.find("COMPANY-DATA-REF").attrib["ID-REF"]

            team_member_ref = cdi.find("TEAM-MEMBER-REF")
            if team_member_ref is not None:
                team_member_ref = team_member_ref.attrib["ID-REF"]

            doc_label = cdi.findtext("DOC-LABEL")

            cdilist.append(CompanyDocInfo(company_data_ref=company_data_ref,
                                          team_member_ref=team_member_ref,
                                          doc_label=doc_label))

        company_doc_infos = cdilist

    doc_revisions = et_element.find("DOC-REVISIONS")
    if doc_revisions is not None:
        drlist = list()
        for dr in doc_revisions.iterfind("DOC-REVISION"):
            team_member_ref = dr.find("TEAM-MEMBER-REF")
            if team_member_ref is not None:
                team_member_ref = team_member_ref.attrib["ID-REF"]

            revision_label = dr.findtext("REVISION-LABEL")
            state = dr.findtext("STATE")
            date = dr.findtext("DATE")
            tool = dr.findtext("TOOL")

            modlist = None
            mods = dr.find("MODIFICATIONS")
            if mods is not None:
                modlist = list()
                for mod in mods.iterfind("MODIFICATION"):
                    m_change = mod.findtext("CHANGE")
                    m_reason = mod.findtext("REASON")
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
