from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment


@dataclass
class ExternalDoc:
    description: str | None
    href: str

    @staticmethod
    def from_et(et_element: ElementTree.Element | None,
                doc_frags: list[OdxDocFragment]) -> Optional["ExternalDoc"]:
        if et_element is None:
            return None

        description = et_element.text
        href = odxrequire(et_element.get("HREF"))

        return ExternalDoc(description=description, href=href)
