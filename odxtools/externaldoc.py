from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment


@dataclass
class ExternalDoc:
    description: Optional[str]
    href: str

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                doc_frags: List[OdxDocFragment]) -> Optional["ExternalDoc"]:
        if et_element is None:
            return None

        description = et_element.text
        href = odxrequire(et_element.get("HREF"))

        return ExternalDoc(description=description, href=href)
