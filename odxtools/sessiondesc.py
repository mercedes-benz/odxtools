# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, cast
from xml.etree import ElementTree

from .audience import Audience
from .direction import Direction
from .element import NamedElement
from .exceptions import odxraise, odxrequire
from .flashclass import FlashClass
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .ownident import OwnIdent
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SessionDesc(NamedElement):
    partnumber: str | None = None
    priority: int | None = None
    session_snref: str
    diag_comm_snref: str | None = None
    flash_class_refs: list[OdxLinkRef] = field(default_factory=list)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    audience: Audience | None = None
    own_ident: OwnIdent | None = None
    oid: str | None = None
    direction: Direction

    @property
    def flash_classes(self) -> NamedItemList[FlashClass]:
        return self._flash_classes

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SessionDesc":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        partnumber = et_element.findtext("PARTNUMBER")
        priority = None
        if (priority_str := et_element.findtext("PRIORITY")) is not None:
            try:
                priority = int(priority_str)
            except Exception as e:
                odxraise(f"Cannot parse PRIORITY: {e}")
        session_snref = None
        if (session_snref_elem := odxrequire(et_element.find("SESSION-SNREF"))) is not None:
            session_snref = odxrequire(session_snref_elem.attrib.get("SHORT-NAME"))
        diag_comm_snref = None
        if (diag_comm_snref_elem := et_element.find("DIAG-COMM-SNREF")) is not None:
            diag_comm_snref = odxrequire(diag_comm_snref_elem.attrib.get("SHORT-NAME"))
        flash_class_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("FLASH-CLASS-REFS/FLASH-CLASS-REF")
        ]
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, context)
        own_ident = None
        if (own_ident_elem := et_element.find("OWN-IDENT")) is not None:
            own_ident = OwnIdent.from_et(own_ident_elem, context)
        direction_str = odxrequire(et_element.attrib.get("DIRECTION"))
        try:
            direction = Direction(direction_str)
        except ValueError:
            odxraise(f"Encountered unknown DIRECTION '{direction_str}'")
            direction = cast(Direction, None)
        oid = et_element.attrib.get("OID")

        return SessionDesc(
            partnumber=partnumber,
            priority=priority,
            session_snref=session_snref,
            diag_comm_snref=diag_comm_snref,
            flash_class_refs=flash_class_refs,
            sdgs=sdgs,
            audience=audience,
            own_ident=own_ident,
            direction=direction,
            oid=oid,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        if self.own_ident is not None:
            odxlinks.update(self.own_ident._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._flash_classes = NamedItemList(
            [odxlinks.resolve(ref, FlashClass) for ref in self.flash_class_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # TODO: resolve session_snref and diag_comm_snref
        pass
