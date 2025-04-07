# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .relateddoc import RelatedDoc
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup


@dataclass(kw_only=True)
class CompanySpecificInfo:
    related_docs: list[RelatedDoc] = field(default_factory=list)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "CompanySpecificInfo":
        related_docs = [
            RelatedDoc.from_et(rd, context)
            for rd in et_element.iterfind("RELATED-DOCS/RELATED-DOC")
        ]

        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return CompanySpecificInfo(related_docs=related_docs, sdgs=sdgs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for rd in self.related_docs:
            result.update(rd._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for rd in self.related_docs:
            rd._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for rd in self.related_docs:
            rd._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
