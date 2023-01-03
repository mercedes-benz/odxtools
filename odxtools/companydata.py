# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .nameditemlist import NamedItemList
from .utils import create_description_from_et
from .odxlink import OdxLinkId, OdxLinkDatabase, OdxDocFragment
from .utils import short_name_as_id
from .specialdata import SpecialDataGroup, create_sdgs_from_et

from xml.etree import ElementTree
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List

@dataclass()
class XDoc:
    short_name : str
    long_name : Optional[str] = None
    description : Optional[str] = None
    number: Optional[str] = None
    state: Optional[str] = None
    date: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    position: Optional[str] = None

    @staticmethod
    def from_et(xdoc) -> "XDoc":
        short_name = xdoc.findtext("SHORT-NAME")
        long_name = xdoc.findtext("LONG-NAME")
        description = create_description_from_et(xdoc.find("DESC"))
        number = xdoc.findtext("NUMBER")
        state = xdoc.findtext("STATE")
        date = xdoc.findtext("DATE")
        publisher = xdoc.findtext("PUBLISHER")
        url = xdoc.findtext("URL")
        position = xdoc.findtext("POSITION")

        return XDoc(short_name=short_name,
                    long_name=long_name,
                    description=description,
                    number=number,
                    state=state,
                    date=date,
                    publisher=publisher,
                    url=url,
                    position=position,
                    )

@dataclass()
class RelatedDoc:
    description: Optional[str] = None
    xdoc: Optional[XDoc] = None

    @staticmethod
    def from_et(et_element) -> "RelatedDoc":
        description = create_description_from_et(et_element.find("DESC"))
        xdoc = et_element.find("XDOC")
        if xdoc is not None:
            xdoc = XDoc.from_et(xdoc)

        return RelatedDoc(description=description,
                          xdoc=xdoc,
                          )


@dataclass()
class CompanySpecificInfo:
    related_docs: Optional[List[RelatedDoc]]
    sdgs: List[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "CompanySpecificInfo":
        related_docs = et_element.find("RELATED-DOCS")
        if related_docs is not None:
            rdlist = list()
            for rd in related_docs.iterfind("RELATED-DOC"):
                rdlist.append(RelatedDoc.from_et(rd))

            related_docs = rdlist

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return CompanySpecificInfo(related_docs=related_docs,
                                   sdgs=sdgs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = { }

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

@dataclass()
class TeamMember:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    department: Optional[str] = None
    address: Optional[str] = None
    zip: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "TeamMember":
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        roles = list()
        if (roles_elem := et_element.find("ROLES")) is not None:
            for role_elem in roles_elem.iterfind("ROLE"):
                role = role_elem.text
                assert role is not None
                roles.append(role)

        department = et_element.findtext("DEPARTMENT")
        address = et_element.findtext("ADDRESS")
        zip = et_element.findtext("ZIP")
        city = et_element.findtext("CITY")
        phone = et_element.findtext("PHONE")
        fax = et_element.findtext("FAX")
        email = et_element.findtext("EMAIL")

        return TeamMember(odx_id=odx_id,
                          short_name=short_name,
                          long_name=long_name,
                          description=description,
                          roles=roles,
                          department=department,
                          address=address,
                          zip=zip,
                          city=city,
                          phone=phone,
                          fax=fax,
                          email=email)


@dataclass()
class CompanyData:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    team_members: Optional[NamedItemList[TeamMember]] = None
    company_specific_info: Optional[CompanySpecificInfo] = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "CompanyData":

        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        roles = et_element.find("ROLES")
        if roles is not None:
            rlist = list()

            for role in roles.iterfind("ROLE"):
                rlist.append(role.text)

            roles = rlist

        team_members = et_element.find("TEAM-MEMBERS")
        if team_members is not None:
            tml = NamedItemList(short_name_as_id) # type: ignore

            for tm in team_members.iterfind("TEAM-MEMBER"):
                tml.append(TeamMember.from_et(tm, doc_frags))

            team_members = tml

        company_specific_info = et_element.find("COMPANY-SPECIFIC-INFO")
        if company_specific_info is not None:
            company_specific_info = CompanySpecificInfo.from_et(company_specific_info, doc_frags)

        return CompanyData(odx_id=odx_id,
                           short_name=short_name,
                           long_name=long_name,
                           description=description,
                           roles=roles,
                           team_members=team_members,
                           company_specific_info=company_specific_info)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = { self.odx_id: self }

        # team members
        if self.team_members is not None:
            for tm in self.team_members:
                result[tm.odx_id] = tm

        if self.company_specific_info:
            result.update(self.company_specific_info._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        if self.company_specific_info:
            self.company_specific_info._resolve_references(odxlinks)

def create_company_datas_from_et(et_element, doc_frags: List[OdxDocFragment]) \
        -> NamedItemList[CompanyData]:
    if et_element is None:
        return NamedItemList(short_name_as_id)

    return NamedItemList(short_name_as_id,
                         [
                             CompanyData.from_et(cd_elem, doc_frags)
                             for cd_elem in et_element.iterfind("COMPANY-DATA")
                         ])
