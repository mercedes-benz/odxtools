# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .nameditemlist import NamedItemList
from .companydata import CompanyData, TeamMember
from .odxlink import OdxLinkId, OdxLinkRef, OdxLinkDatabase, OdxDocFragment
from .utils import read_description_from_odx
from .specialdata import SpecialDataGroup, read_sdgs_from_odx

from xml.etree import ElementTree
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

@dataclass()
class CompanyDocInfo:
    company_data_ref: OdxLinkRef
    company_data: Optional[CompanyData] = None
    team_member_ref: Optional[OdxLinkRef] = None
    doc_label: Optional[str] = None
    sdgs: List[SpecialDataGroup] = field(default_factory=list)

    _team_member: Optional[TeamMember] = None
    @property
    def team_member(self) -> Optional[TeamMember]:
        return self._team_member

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = { }

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self.company_data = odxlinks.resolve(self.company_data_ref)

        if self.team_member_ref is not None:
            self._team_member = odxlinks.resolve(self.team_member_ref)

        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

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
    company_doc_infos: List[CompanyDocInfo] = field(default_factory=list)
    doc_revisions: Optional[List[DocRevision]] = None

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        for cdi in self.company_doc_infos:
            result.update(cdi._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        if self.company_doc_infos is not None:
            for cdi in self.company_doc_infos:
                cdi._resolve_references(odxlinks)

        if self.doc_revisions is not None:
            for dr in self.doc_revisions:
                dr._resolve_references(odxlinks)

        for cdi in self.company_doc_infos:
            cdi._resolve_references(odxlinks)

def read_admin_data_from_odx(et_element: Optional[ElementTree.Element],
                             doc_frags: List[OdxDocFragment]) \
        -> Optional[AdminData]:

    if et_element is None:
        return None

    language = et_element.findtext("LANGUAGE")

    company_doc_infos = list()
    if cdis_elem := et_element.find("COMPANY-DOC-INFOS"):
        for cdi in cdis_elem.iterfind("COMPANY-DOC-INFO"):
            # the company data reference is mandatory
            company_data_ref = OdxLinkRef.from_et(cdi.find("COMPANY-DATA-REF"), doc_frags)
            assert company_data_ref is not None
            team_member_ref = OdxLinkRef.from_et(cdi.find("TEAM-MEMBER-REF"), doc_frags)
            doc_label = cdi.findtext("DOC-LABEL")
            sdgs = read_sdgs_from_odx(cdi.find("SDGS"), doc_frags)

            company_doc_infos.append(CompanyDocInfo(company_data_ref=company_data_ref,
                                                    team_member_ref=team_member_ref,
                                                    doc_label=doc_label,
                                                    sdgs=sdgs))

    doc_revisions = []
    if drs_elem := et_element.find("DOC-REVISIONS"):
        for dr in drs_elem.iterfind("DOC-REVISION"):
            team_member_ref = OdxLinkRef.from_et(dr.find("TEAM-MEMBER-REF"), doc_frags)
            revision_label = dr.findtext("REVISION-LABEL")
            state = dr.findtext("STATE")
            date = dr.findtext("DATE")
            assert date is not None
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

            doc_revisions.append(DocRevision(team_member_ref=team_member_ref,
                                      revision_label=revision_label,
                                      state=state,
                                      date=date,
                                      tool=tool,
                                      modifications=modlist))

    return AdminData(language=language,
                     company_doc_infos=company_doc_infos,
                     doc_revisions=doc_revisions)
