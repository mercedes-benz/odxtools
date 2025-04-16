from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext


@dataclass(kw_only=True)
class ExternalDoc:
    description: str | None = None
    href: str

    @staticmethod
    def from_et(et_element: ElementTree.Element | None,
                context: OdxDocContext) -> Optional["ExternalDoc"]:
        if et_element is None:
            return None

        description = et_element.text
        href = odxrequire(et_element.get("HREF"))

        return ExternalDoc(description=description, href=href)
