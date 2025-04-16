# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .element import NamedElement
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SwVariable(NamedElement):
    origin: str | None = None
    oid: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SwVariable":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        origin = et_element.findtext("ORIGIN")
        oid = et_element.attrib.get("OID")

        return SwVariable(origin=origin, oid=oid, **kwargs)
