# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .companyspecificinfo import CompanySpecificInfo
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .teammember import TeamMember
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


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
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "CompanyData":

        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        roles = []
        if (roles_elem := et_element.find("ROLES")) is not None:
            roles = [odxrequire(role.text) for role in roles_elem.iterfind("ROLE")]

        team_members = [
            TeamMember.from_et(tm, doc_frags)
            for tm in et_element.iterfind("TEAM-MEMBERS/TEAM-MEMBER")
        ]
        company_specific_info = None
        if (company_specific_info_elem := et_element.find("COMPANY-SPECIFIC-INFO")) is not None:
            company_specific_info = CompanySpecificInfo.from_et(company_specific_info_elem,
                                                                doc_frags)

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
