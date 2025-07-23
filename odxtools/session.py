# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .checksum import Checksum
from .datablock import Datablock
from .element import IdentifiableElement
from .expectedident import ExpectedIdent
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .security import Security
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class Session(IdentifiableElement):
    expected_idents: NamedItemList[ExpectedIdent] = field(default_factory=NamedItemList)
    checksums: NamedItemList[Checksum] = field(default_factory=NamedItemList)
    securities: list[Security] = field(default_factory=list)
    datablock_refs: list[OdxLinkRef] = field(default_factory=list)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @property
    def datablocks(self) -> NamedItemList[Datablock]:
        return self._datablocks

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Session":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        expected_idents = NamedItemList([
            ExpectedIdent.from_et(el, context)
            for el in et_element.iterfind("EXPECTED-IDENTS/EXPECTED-IDENT")
        ])
        checksums = NamedItemList(
            [Checksum.from_et(el, context) for el in et_element.iterfind("CHECKSUMS/CHECKSUM")])
        securities = [
            Security.from_et(el, context) for el in et_element.iterfind("SECURITYS/SECURITY")
        ]
        datablock_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("DATABLOCK-REFS/DATABLOCK-REF")
        ]
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return Session(
            expected_idents=expected_idents,
            checksums=checksums,
            securities=securities,
            datablock_refs=datablock_refs,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for ei in self.expected_idents:
            odxlinks.update(ei._build_odxlinks())
        for cs in self.checksums:
            odxlinks.update(cs._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._datablocks = NamedItemList(
            [odxlinks.resolve(ref, Datablock) for ref in self.datablock_refs])

        for ei in self.expected_idents:
            ei._resolve_odxlinks(odxlinks)
        for cs in self.checksums:
            cs._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for ei in self.expected_idents:
            ei._resolve_snrefs(context)
        for cs in self.checksums:
            cs._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
