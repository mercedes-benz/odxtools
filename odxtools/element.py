from dataclasses import dataclass
from xml.etree import ElementTree

from .description import Description
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkId
from .utils import dataclass_fields_asdict


@dataclass
class NamedElement:
    short_name: str
    long_name: str | None
    description: Description | None

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: list[OdxDocFragment]) -> "NamedElement":

        return NamedElement(
            short_name=odxrequire(et_element.findtext("SHORT-NAME")),
            long_name=et_element.findtext("LONG-NAME"),
            description=Description.from_et(et_element.find("DESC"), doc_frags),
        )


@dataclass
class IdentifiableElement(NamedElement):
    odx_id: OdxLinkId
    oid: str | None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: list[OdxDocFragment]) -> "IdentifiableElement":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        oid = et_element.get("OID")

        return IdentifiableElement(**kwargs, odx_id=odx_id, oid=oid)
