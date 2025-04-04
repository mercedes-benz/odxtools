# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkRef
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class RelatedDiagCommRef(OdxLinkRef):
    relation_type: str

    @staticmethod
    def from_et(  # type: ignore[override]
            et_element: ElementTree.Element, context: OdxDocContext) -> "RelatedDiagCommRef":
        kwargs = dataclass_fields_asdict(odxrequire(OdxLinkRef.from_et(et_element, context)))

        relation_type = odxrequire(et_element.findtext("RELATION-TYPE"))

        return RelatedDiagCommRef(relation_type=relation_type, **kwargs)
