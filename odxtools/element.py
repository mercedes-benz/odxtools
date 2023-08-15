from dataclasses import dataclass
from typing import List, Optional, TypedDict, cast
from xml.etree import ElementTree

from odxtools.exceptions import odxrequire
from odxtools.utils import create_description_from_et

from .odxlink import OdxDocFragment, OdxLinkId


class BaseElementKwargs(TypedDict):
    short_name: str
    long_name: Optional[str]
    description: Optional[str]


@dataclass
class BaseElement:
    short_name: str
    long_name: Optional[str]
    description: Optional[str]

    @staticmethod
    def get_kwargs(
        et_element: ElementTree.Element,
        doc_frags: List[OdxDocFragment],
    ) -> BaseElementKwargs:

        return dict(
            short_name=odxrequire(et_element.findtext("SHORT-NAME")),
            long_name=et_element.findtext("LONG-NAME"),
            description=create_description_from_et(et_element.find("DESC")),
        )


class IdentifiableElementKwargs(BaseElementKwargs):
    odx_id: OdxLinkId


@dataclass
class IdentifiableElement(BaseElement):
    odx_id: OdxLinkId

    @staticmethod
    def get_kwargs(
        et_element: ElementTree.Element,
        doc_frags: List[OdxDocFragment],
    ) -> IdentifiableElementKwargs:

        kwargs = cast(IdentifiableElementKwargs, BaseElement.get_kwargs(et_element, doc_frags))
        kwargs['odx_id'] = odxrequire(OdxLinkId.from_et(et_element, doc_frags))

        return kwargs
