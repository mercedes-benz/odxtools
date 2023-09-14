from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkId
from .utils import create_description_from_et, dataclass_fields_asdict


@dataclass
class NamedElement:
    short_name: str
    long_name: Optional[str]
    description: Optional[str]

    @staticmethod
    def from_et(
        et_element: ElementTree.Element,
        doc_frags: List[OdxDocFragment],
    ) -> "NamedElement":

        return NamedElement(
            short_name=odxrequire(et_element.findtext("SHORT-NAME")),
            long_name=et_element.findtext("LONG-NAME"),
            description=create_description_from_et(et_element.find("DESC")),
        )


@dataclass
class IdentifiableElement(NamedElement):
    odx_id: OdxLinkId

    @staticmethod
    def from_et(
        et_element: ElementTree.Element,
        doc_frags: List[OdxDocFragment],
    ) -> "IdentifiableElement":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))
        return IdentifiableElement(
            **kwargs,
            odx_id=odxrequire(OdxLinkId.from_et(et_element, doc_frags)),
        )
