# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .datablock import Datablock
from .exceptions import odxraise
from .externflashdata import ExternFlashdata
from .flashdata import Flashdata
from .globals import xsi
from .internflashdata import InternFlashdata
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .session import Session
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class Mem:
    sessions: NamedItemList[Session]
    datablocks: NamedItemList[Datablock]
    flashdatas: NamedItemList[Flashdata]

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Mem":
        sessions = NamedItemList([
            Session.from_et(sess_elem, context)
            for sess_elem in et_element.iterfind("SESSIONS/SESSION")
        ])

        datablocks = NamedItemList([
            Datablock.from_et(db_elem, context)
            for db_elem in et_element.iterfind("DATABLOCKS/DATABLOCK")
        ])

        flashdatas: NamedItemList[Flashdata] = NamedItemList()
        for flashdata_elem in et_element.iterfind("FLASHDATAS/FLASHDATA"):
            flashdata_type = flashdata_elem.attrib.get(f"{xsi}type")
            if flashdata_type == "INTERN-FLASHDATA":
                flashdatas.append(InternFlashdata.from_et(flashdata_elem, context))
            elif flashdata_type == "EXTERN-FLASHDATA":
                flashdatas.append(ExternFlashdata.from_et(flashdata_elem, context))
            else:
                odxraise(f"Encountered unknown flashdata type {flashdata_type}")
                flashdatas.append(Flashdata.from_et(flashdata_elem, context))

        return Mem(
            sessions=sessions,
            datablocks=datablocks,
            flashdatas=flashdatas,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {}

        for session in self.sessions:
            odxlinks.update(session._build_odxlinks())
        for datablock in self.datablocks:
            odxlinks.update(datablock._build_odxlinks())
        for flashdata in self.flashdatas:
            odxlinks.update(flashdata._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for session in self.sessions:
            session._resolve_odxlinks(odxlinks)
        for datablock in self.datablocks:
            datablock._resolve_odxlinks(odxlinks)
        for flashdata in self.flashdatas:
            flashdata._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for session in self.sessions:
            session._resolve_snrefs(context)
        for datablock in self.datablocks:
            datablock._resolve_snrefs(context)
        for flashdata in self.flashdatas:
            flashdata._resolve_snrefs(context)
