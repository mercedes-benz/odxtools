# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .groupmember import GroupMember
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class EcuGroup(NamedElement):
    group_members: list[GroupMember]
    oid: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuGroup":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        group_members = [
            GroupMember.from_et(el, context)
            for el in et_element.iterfind("GROUP-MEMBERS/GROUP-MEMBER")
        ]
        oid = et_element.attrib.get("OID")

        return EcuGroup(group_members=group_members, oid=oid, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {}

        for gm in self.group_members:
            odxlinks.update(gm._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for gm in self.group_members:
            gm._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for gm in self.group_members:
            gm._resolve_snrefs(context)
