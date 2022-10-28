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
    short_name = xdoc.find("SHORT-NAME").text

    long_name = xdoc.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text

    description = xdoc.find("DESC")
    if description is not None:
        description = read_description_from_odx(description)

    number = xdoc.find("NUMBER")
    if number is not None:
        number = number.text

    state = xdoc.find("STATE")
    if state is not None:
        state = state.text

    date = xdoc.find("DATE")
    if date is not None:
        date = date.text

    publisher = xdoc.find("PUBLISHER")
    if publisher is not None:
        publisher = publisher.text

    url = xdoc.find("URL")
    if url is not None:
        url = url.text

    position = xdoc.find("POSITION")
    if position is not None:
        position = position.text

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

def read_company_datas_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    if et_element is None:
        return None

    cdl = NamedItemList(short_name_as_id) # type: ignore

    for cd in et_element.iterfind("COMPANY-DATA"):
        odx_id = OdxLinkId.from_et(cd, doc_frags)
        assert odx_id is not None
        short_name = cd.find("SHORT-NAME").text

        long_name = cd.find("LONG-NAME")
        if long_name is not None:
            long_name = long_name.text

        description = cd.find("DESC")
        if description is not None:
            description = read_description_from_odx(description)

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
                tm_short_name = tm.find("SHORT-NAME").text

                tm_long_name = tm.find("LONG-NAME")
                if tm_long_name is not None:
                    tm_long_name = tm_long_name.text

                tm_description = tm.find("DESC")
                if tm_description is not None:
                    tm_description = read_description_from_odx(tm_description)

                tm_roles = tm.find("ROLES")
                if tm_roles is not None:
                    rlist = list()
                    for role in tm_roles.iterfind("ROLE"):
                        rlist.append(role.text)
                    tm_roles = rlist

                tm_department = tm.find("DEPARTMENT")
                if tm_department is not None:
                    tm_department = tm_department.text

                tm_address = tm.find("ADDRESS")
                if tm_address is not None:
                    tm_address = tm_address.text

                tm_zip = tm.find("ZIP")
                if tm_zip is not None:
                    tm_zip = tm_zip.text

                tm_city = tm.find("CITY")
                if tm_city is not None:
                    tm_city = tm_city.text

                tm_phone = tm.find("PHONE")
                if tm_phone is not None:
                    tm_phone = tm_phone.text

                tm_fax = tm.find("FAX")
                if tm_fax is not None:
                    tm_fax = tm_fax.text

                tm_email = tm.find("EMAIL")
                if tm_email is not None:
                    tm_email = tm_email.text

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
                    rd_description = rd.find("DESC")
                    if rd_description is not None:
                        rd_description = read_description_from_odx(rd_description)

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
