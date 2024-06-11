# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .companyspecificinfo import CompanySpecificInfo
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .teammember import TeamMember
from .utils import dataclass_fields_asdict


@dataclass
class CompanyData(IdentifiableElement):
    roles: List[str]
    team_members: NamedItemList[TeamMember]
    company_specific_info: Optional[CompanySpecificInfo]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "CompanyData":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
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
            roles=roles,
            team_members=NamedItemList(team_members),
            company_specific_info=company_specific_info,
            **kwargs,
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

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for tm in self.team_members:
            tm._resolve_snrefs(context)

        if self.company_specific_info:
            self.company_specific_info._resolve_snrefs(context)
