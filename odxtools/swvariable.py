# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .element import NamedElement
from .odxlink import OdxDocFragment
from .utils import dataclass_fields_asdict


@dataclass
class SwVariable(NamedElement):
    origin: str | None
    oid: str | None

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: list[OdxDocFragment]) -> "SwVariable":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        origin = et_element.findtext("ORIGIN")
        oid = et_element.attrib.get("OID")

        return SwVariable(origin=origin, oid=oid, **kwargs)
