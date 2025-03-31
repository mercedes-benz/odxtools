# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkRef
from .utils import dataclass_fields_asdict


@dataclass
class RelatedDiagCommRef(OdxLinkRef):
    relation_type: str

    @staticmethod
    def from_et(  # type: ignore[override]
            et_element: ElementTree.Element,
            doc_frags: List[OdxDocFragment]) -> "RelatedDiagCommRef":
        kwargs = dataclass_fields_asdict(odxrequire(OdxLinkRef.from_et(et_element, doc_frags)))

        relation_type = odxrequire(et_element.findtext("RELATION-TYPE"))

        return RelatedDiagCommRef(relation_type=relation_type, **kwargs)
