# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class XDoc:
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    number: Optional[str]
    state: Optional[str]
    date: Optional[str]
    publisher: Optional[str]
    url: Optional[str]
    position: Optional[str]

    @staticmethod
    def from_et(et_element) -> "XDoc":
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        number = et_element.findtext("NUMBER")
        state = et_element.findtext("STATE")
        date = et_element.findtext("DATE")
        publisher = et_element.findtext("PUBLISHER")
        url = et_element.findtext("URL")
        position = et_element.findtext("POSITION")

        return XDoc(
            short_name=short_name,
            long_name=long_name,
            description=description,
            number=number,
            state=state,
            date=date,
            publisher=publisher,
            url=url,
            position=position,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass


@dataclass
class RelatedDoc:
    description: Optional[str]
    xdoc: Optional[XDoc]

    @staticmethod
    def from_et(et_element) -> "RelatedDoc":
        description = create_description_from_et(et_element.find("DESC"))
        xdoc = et_element.find("XDOC")
        if xdoc is not None:
            xdoc = XDoc.from_et(xdoc)

        return RelatedDoc(
            description=description,
            xdoc=xdoc,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        if self.xdoc:
            result.update(self.xdoc._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.xdoc:
            self.xdoc._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.xdoc:
            self.xdoc._resolve_snrefs(diag_layer)


@dataclass
class CompanySpecificInfo:
    related_docs: List[RelatedDoc]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "CompanySpecificInfo":
        related_docs = [
            RelatedDoc.from_et(rd) for rd in et_element.iterfind("RELATED-DOCS/RELATED-DOC")
        ]

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return CompanySpecificInfo(related_docs=related_docs, sdgs=sdgs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for rd in self.related_docs:
            rd._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for rd in self.related_docs:
            rd._resolve_snrefs(diag_layer)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)


@dataclass
class TeamMember:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    roles: List[str]
    department: Optional[str]
    address: Optional[str]
    zip: Optional[str]
    city: Optional[str]
    phone: Optional[str]
    fax: Optional[str]
    email: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "TeamMember":
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

        return TeamMember(
            odx_id=odx_id,
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
            email=email,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass


@dataclass
class CompanyData:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    roles: List[str]
    team_members: NamedItemList[TeamMember]
    company_specific_info: Optional[CompanySpecificInfo]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "CompanyData":

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

        team_members = [
            TeamMember.from_et(tm, doc_frags)
            for tm in et_element.iterfind("TEAM-MEMBERS/TEAM-MEMBER")
        ]
        company_specific_info = et_element.find("COMPANY-SPECIFIC-INFO")
        if company_specific_info is not None:
            company_specific_info = CompanySpecificInfo.from_et(company_specific_info, doc_frags)

        return CompanyData(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            roles=roles,
            team_members=NamedItemList(short_name_as_id, team_members),
            company_specific_info=company_specific_info,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        # team members
        for tm in self.team_members:
            result.update(tm._build_odxlinks())

        if self.company_specific_info:
            result.update(self.company_specific_info._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for tm in self.team_members:
            tm._resolve_odxlinks(odxlinks)

        if self.company_specific_info:
            self.company_specific_info._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for tm in self.team_members:
            tm._resolve_snrefs(diag_layer)

        if self.company_specific_info:
            self.company_specific_info._resolve_snrefs(diag_layer)


def create_company_datas_from_et(et_element,
                                 doc_frags: List[OdxDocFragment]) -> NamedItemList[CompanyData]:
    if et_element is None:
        return NamedItemList(short_name_as_id)

    return NamedItemList(
        short_name_as_id,
        [
            CompanyData.from_et(cd_elem, doc_frags)
            for cd_elem in et_element.iterfind("COMPANY-DATA")
        ],
    )
