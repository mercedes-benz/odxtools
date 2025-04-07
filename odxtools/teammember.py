# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class TeamMember(IdentifiableElement):
    roles: list[str] = field(default_factory=list)
    department: str | None = None
    address: str | None = None
    zipcode: str | None = None  # the tag for this is "ZIP", but `zip` is a keyword in python
    city: str | None = None
    phone: str | None = None
    fax: str | None = None
    email: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "TeamMember":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        roles = [odxrequire(role_elem.text) for role_elem in et_element.iterfind("ROLES/ROLE")]
        department = et_element.findtext("DEPARTMENT")
        address = et_element.findtext("ADDRESS")
        zipcode = et_element.findtext("ZIP")
        city = et_element.findtext("CITY")
        phone = et_element.findtext("PHONE")
        fax = et_element.findtext("FAX")
        email = et_element.findtext("EMAIL")

        return TeamMember(
            roles=roles,
            department=department,
            address=address,
            zipcode=zipcode,
            city=city,
            phone=phone,
            fax=fax,
            email=email,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
