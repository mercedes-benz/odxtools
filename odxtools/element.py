from dataclasses import dataclass
from xml.etree import ElementTree

from .description import Description
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkId
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class NamedElement:
    short_name: str
    long_name: str | None = None
    description: Description | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "NamedElement":

        return NamedElement(
            short_name=odxrequire(et_element.findtext("SHORT-NAME")),
            long_name=et_element.findtext("LONG-NAME"),
            description=Description.from_et(et_element.find("DESC"), context),
        )


@dataclass(kw_only=True)
class IdentifiableElement(NamedElement):
    odx_id: OdxLinkId
    oid: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "IdentifiableElement":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        odx_id = odxrequire(OdxLinkId.from_et(et_element, context))
        oid = et_element.get("OID")

        return IdentifiableElement(**kwargs, odx_id=odx_id, oid=oid)
