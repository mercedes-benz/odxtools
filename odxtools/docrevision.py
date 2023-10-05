# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .companyrevisioninfo import CompanyRevisionInfo
from .exceptions import odxrequire
from .modification import Modification
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .teammember import TeamMember

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DocRevision:
    """
    Representation of a single revision of the relevant object.
    """

    date: str
    team_member_ref: Optional[OdxLinkRef]
    revision_label: Optional[str]
    state: Optional[str]
    tool: Optional[str]
    company_revision_infos: List[CompanyRevisionInfo]
    modifications: List[Modification]

    @property
    def team_member(self) -> Optional[TeamMember]:
        return self._team_member

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DocRevision":

        team_member_ref = OdxLinkRef.from_et(et_element.find("TEAM-MEMBER-REF"), doc_frags)
        revision_label = et_element.findtext("REVISION-LABEL")
        state = et_element.findtext("STATE")
        date = odxrequire(et_element.findtext("DATE"))
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

        return DocRevision(
            team_member_ref=team_member_ref,
            revision_label=revision_label,
            state=state,
            date=date,
            tool=tool,
            company_revision_infos=crilist,
            modifications=modlist,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._team_member: Optional[TeamMember] = None
        if self.team_member_ref is not None:
            self._team_member = odxlinks.resolve(self.team_member_ref, TeamMember)

        for cri in self.company_revision_infos:
            cri._resolve_odxlinks(odxlinks)

        for mod in self.modifications:
            mod._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for cri in self.company_revision_infos:
            cri._resolve_snrefs(diag_layer)

        for mod in self.modifications:
            mod._resolve_snrefs(diag_layer)
