# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from .createsdgs import create_sdgs_from_et
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .relateddoc import RelatedDoc
from .specialdatagroup import SpecialDataGroup

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class CompanySpecificInfo:
    related_docs: List[RelatedDoc]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "CompanySpecificInfo":
        related_docs = [
            RelatedDoc.from_et(rd, doc_frags)
            for rd in et_element.iterfind("RELATED-DOCS/RELATED-DOC")
        ]

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return CompanySpecificInfo(related_docs=related_docs, sdgs=sdgs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for rd in self.related_docs:
            rd._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for rd in self.related_docs:
            rd._resolve_snrefs(diag_layer)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
