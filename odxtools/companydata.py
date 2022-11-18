# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .nameditemlist import NamedItemList
from .utils import read_description_from_odx
from .odxlink import OdxLinkId, OdxLinkDatabase, OdxDocFragment
from .utils import short_name_as_id

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

@dataclass()
class RelatedDoc:
    description: Optional[str] = None
    xdoc: Optional[XDoc] = None

@dataclass()
class CompanySpecificInfo:
    related_docs: Optional[List[RelatedDoc]]

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

@dataclass()
class CompanyData:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    team_members: Optional[NamedItemList[TeamMember]] = None
    company_specific_info: Optional[CompanySpecificInfo] = None

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = { self.odx_id: self }

        # team members
        if self.team_members is not None:
            for tm in self.team_members:
                result[tm.odx_id] = tm

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        pass

def read_xdoc_from_odx(xdoc):
    short_name = xdoc.findtext("SHORT-NAME")
    long_name = xdoc.findtext("LONG-NAME")
    description = read_description_from_odx(xdoc.find("DESC"))
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

def read_company_datas_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
        -> NamedItemList[CompanyData]:
    if et_element is None:
        return NamedItemList(short_name_as_id)

    cdl = NamedItemList(short_name_as_id) # type: ignore

    for cd in et_element.iterfind("COMPANY-DATA"):
        odx_id = OdxLinkId.from_et(cd, doc_frags)
        assert odx_id is not None
        short_name = cd.findtext("SHORT-NAME")
        long_name = cd.findtext("LONG-NAME")
        description = read_description_from_odx(cd.find("DESC"))
        roles = cd.find("ROLES")
        if roles is not None:
            rlist = list()

            for role in roles.iterfind("ROLE"):
                rlist.append(role.text)

            roles = rlist

        team_members = cd.find("TEAM-MEMBERS")
        if team_members is not None:
            tml = NamedItemList(short_name_as_id) # type: ignore

            for tm in team_members.iterfind("TEAM-MEMBER"):
                tm_id = OdxLinkId.from_et(tm, doc_frags)
                assert tm_id is not None
                tm_short_name = tm.findtext("SHORT-NAME")
                tm_long_name = tm.findtext("LONG-NAME")
                tm_description = read_description_from_odx(tm.find("DESC"))

                tm_roles = tm.find("ROLES")
                if tm_roles is not None:
                    rlist = list()
                    for role in tm_roles.iterfind("ROLE"):
                        rlist.append(role.text)
                    tm_roles = rlist

                tm_department = tm.findtext("DEPARTMENT")
                tm_address = tm.findtext("ADDRESS")
                tm_zip = tm.findtext("ZIP")
                tm_city = tm.findtext("CITY")
                tm_phone = tm.findtext("PHONE")
                tm_fax = tm.findtext("FAX")
                tm_email = tm.findtext("EMAIL")

                tml.append(TeamMember(odx_id=tm_id,
                                      short_name=tm_short_name,
                                      long_name=tm_long_name,
                                      description=tm_description,
                                      roles=tm_roles,
                                      department=tm_department,
                                      address=tm_address,
                                      zip=tm_zip,
                                      city=tm_city,
                                      phone=tm_phone,
                                      fax=tm_fax,
                                      email=tm_email))

            team_members = tml

        company_specific_info = cd.find("COMPANY-SPECIFIC-INFO")
        if company_specific_info is not None:
            related_docs = company_specific_info.find("RELATED-DOCS")
            if related_docs is not None:
                rdlist = list()
                for rd in related_docs.iterfind("RELATED-DOC"):
                    rd_description = read_description_from_odx(rd.find("DESC"))
                    xdoc = rd.find("XDOC")
                    if xdoc is not None:
                        xdoc = read_xdoc_from_odx(xdoc)

                    rdlist.append(RelatedDoc(description=rd_description,
                                             xdoc=xdoc,
                                             ))

                related_docs = rdlist

            company_specific_info = CompanySpecificInfo(related_docs=related_docs)

        cdl.append(CompanyData(odx_id=odx_id,
                               short_name=short_name,
                               long_name=long_name,
                               description=description,
                               roles=roles,
                               team_members=team_members,
                               company_specific_info=company_specific_info))

    return cdl
