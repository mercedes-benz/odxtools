# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .nameditemlist import NamedItemList
from .companydata import CompanyData, TeamMember
from .odxlink import OdxLinkId, OdxLinkRef, OdxLinkDatabase, OdxDocFragment
from .utils import create_description_from_et
from .specialdata import SpecialDataGroup, create_sdgs_from_et

from xml.etree import ElementTree
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

@dataclass()
class CompanyDocInfo:
    company_data_ref: OdxLinkRef
    team_member_ref: Optional[OdxLinkRef] = None
    doc_label: Optional[str] = None
    sdgs: List[SpecialDataGroup] = field(default_factory=list)

    _company_data: Optional[CompanyData] = None
    @property
    def company_data(self) -> CompanyData:
        assert self._company_data is not None
        return self._company_data

    _team_member: Optional[TeamMember] = None
    @property
    def team_member(self) -> Optional[TeamMember]:
        return self._team_member

    @staticmethod
    def from_et(et_element: ElementTree.Element ,
                doc_frags: List[OdxDocFragment]) \
            -> "CompanyDocInfo" :
        # the company data reference is mandatory
        company_data_ref = OdxLinkRef.from_et(et_element.find("COMPANY-DATA-REF"), doc_frags)
        assert company_data_ref is not None
        team_member_ref = OdxLinkRef.from_et(et_element.find("TEAM-MEMBER-REF"), doc_frags)
        doc_label = et_element.findtext("DOC-LABEL")
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return CompanyDocInfo(company_data_ref=company_data_ref,
                              team_member_ref=team_member_ref,
                              doc_label=doc_label,
                              sdgs=sdgs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = { }

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self._company_data = odxlinks.resolve(self.company_data_ref)

        if self.team_member_ref is not None:
            self._team_member = odxlinks.resolve(self.team_member_ref)

        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

@dataclass()
class Modification:
    change: Optional[str] = None
    reason: Optional[str] = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) \
            -> "Modification":
        change = et_element.findtext("CHANGE")
        reason = et_element.findtext("REASON")

        return Modification(change=change,
                            reason=reason)

@dataclass()
class CompanyRevisionInfo:
    company_data_ref: OdxLinkRef
    revision_label: Optional[str] = None
    state: Optional[str] = None

    _company_data: Optional[CompanyData] = None
    @property
    def company_data(self) -> CompanyData:
        assert self._company_data is not None
        return self._company_data

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) \
            -> "CompanyRevisionInfo":

        company_data_ref = OdxLinkRef.from_et(et_element.find("COMPANY-DATA-REF"),
                                              doc_frags)
        assert company_data_ref is not None
        revision_label = et_element.findtext("REVISION_LABEL")
        state = et_element.findtext("STATE")

        return CompanyRevisionInfo(company_data_ref=company_data_ref,
                                   revision_label=revision_label,
                                   state=state)

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        cd = odxlinks.resolve(self.company_data_ref)
        assert isinstance(cd, CompanyData)
        self._company_data = cd

@dataclass()
class DocRevision:
    """
    Representation of a single revision of the relevant object.
    """
    date: str
    team_member_ref: Optional[OdxLinkRef] = None
    revision_label: Optional[str] = None
    state: Optional[str] = None
    tool: Optional[str] = None
    company_revision_infos: List[CompanyRevisionInfo] = field(default_factory=list)
    modifications: List[Modification] = field(default_factory=list)

    _team_member: Optional[TeamMember] = None
    @property
    def team_member(self) -> Optional[TeamMember]:
        return self._team_member

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) \
            -> "DocRevision":

        team_member_ref = OdxLinkRef.from_et(et_element.find("TEAM-MEMBER-REF"), doc_frags)
        revision_label = et_element.findtext("REVISION-LABEL")
        state = et_element.findtext("STATE")
        date = et_element.findtext("DATE")
        assert date is not None
        tool = et_element.findtext("TOOL")

        crilist = [
            CompanyRevisionInfo.from_et(cri_elem, doc_frags)
            for cri_elem in et_element.iterfind("COMPANY-REVISION-INFOS/"
                                                "COMPANY-REVISION-INFO")
        ]

        modlist = [
            Modification.from_et(mod_elem, doc_frags)
            for mod_elem in et_element.iterfind("MODIFICATIONS/MODIFICATION")
        ]

        return DocRevision(team_member_ref=team_member_ref,
                           revision_label=revision_label,
                           state=state,
                           date=date,
                           tool=tool,
                           company_revision_infos=crilist,
                           modifications=modlist)

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        if self.team_member_ref is not None:
            self._team_member = odxlinks.resolve(self.team_member_ref)

        for cri in self.company_revision_infos:
            cri._resolve_references(odxlinks)

@dataclass()
class AdminData:
    language: Optional[str] = None
    company_doc_infos: List[CompanyDocInfo] = field(default_factory=list)
    doc_revisions: List[DocRevision] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                doc_frags: List[OdxDocFragment]) \
            -> Optional["AdminData"]:

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

        return AdminData(language=language,
                         company_doc_infos=company_doc_infos,
                         doc_revisions=doc_revisions)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        for cdi in self.company_doc_infos:
            result.update(cdi._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        for cdi in self.company_doc_infos:
            cdi._resolve_references(odxlinks)

        for dr in self.doc_revisions:
            dr._resolve_references(odxlinks)
