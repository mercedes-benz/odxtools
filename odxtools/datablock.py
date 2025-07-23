# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .addrdeffilter import AddrdefFilter
from .audience import Audience
from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .filter import Filter
from .flashdata import Flashdata
from .globals import xsi
from .nameditemlist import NamedItemList
from .negoffset import NegOffset
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .ownident import OwnIdent
from .posoffset import PosOffset
from .security import Security
from .segment import Segment
from .sizedeffilter import SizedefFilter
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .targetaddroffset import TargetAddrOffset
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class Datablock(IdentifiableElement):
    logical_block_index: int | None = None
    flashdata_ref: OdxLinkRef | None = None
    filters: list[Filter] = field(default_factory=list)
    segments: NamedItemList[Segment] = field(default_factory=NamedItemList)

    # the specification does not define the content of
    # TARGET-ADDR-OFFSET, i.e., if it is defined, it must be one of
    # its specializations
    target_addr_offset: TargetAddrOffset | None = None

    own_idents: NamedItemList[OwnIdent] = field(default_factory=NamedItemList)
    securities: list[Security] = field(default_factory=list)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    audience: Audience | None = None

    # note that the spec says this attribute is named "TYPE", but in
    # python, "type" is a build-in function...
    data_type: str

    @property
    def flashdata(self) -> Flashdata | None:
        return self._flashdata

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Datablock":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        logical_block_index = read_hex_binary(et_element.find("LOGICAL-BLOCK-INDEX"))
        flashdata_ref = OdxLinkRef.from_et(et_element.find("FLASHDATA-REF"), context)
        filters: list[Filter] = []
        for filter_elem in et_element.iterfind("FILTERS/FILTER"):
            filter_type = filter_elem.attrib.get(f"{xsi}type")
            if filter_type == "ADDRDEF-FILTER":
                filters.append(AddrdefFilter.from_et(filter_elem, context))
            elif filter_type == "SIZEDEF-FILTER":
                filters.append(SizedefFilter.from_et(filter_elem, context))
            else:
                odxraise(f"Encountered filter of illegal type {filter_type}")
                filters.append(Filter.from_et(filter_elem, context))
        segments = NamedItemList([
            Segment.from_et(segment_elem, context)
            for segment_elem in et_element.iterfind("SEGMENTS/SEGMENT")
        ])
        target_addr_offset: TargetAddrOffset | None = None
        if (tao_elem := et_element.find("TARGET-ADDR-OFFSET")) is not None:
            tao_type = tao_elem.attrib.get(f"{xsi}type")
            if tao_type == "POS-OFFSET":
                target_addr_offset = PosOffset.from_et(tao_elem, context)
            elif tao_type == "NEG-OFFSET":
                target_addr_offset = NegOffset.from_et(tao_elem, context)
            else:
                odxraise(f"Unknown TARGET-ADDR-OFFSET type '{tao_type}'")

        own_idents = NamedItemList([
            OwnIdent.from_et(own_ident_elem, context)
            for own_ident_elem in et_element.iterfind("OWN-IDENTS/OWN-IDENT")
        ])
        securities = [
            Security.from_et(security_elem, context)
            for security_elem in et_element.iterfind("SECURITYS/SECURITY")
        ]
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, context)
        data_type = odxrequire(et_element.attrib.get("TYPE"))

        return Datablock(
            logical_block_index=logical_block_index,
            flashdata_ref=flashdata_ref,
            filters=filters,
            segments=segments,
            own_idents=own_idents,
            securities=securities,
            target_addr_offset=target_addr_offset,
            sdgs=sdgs,
            audience=audience,
            data_type=data_type,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for odxfilter in self.filters:
            odxlinks.update(odxfilter._build_odxlinks())
        for segment in self.segments:
            odxlinks.update(segment._build_odxlinks())
        for own_indent in self.own_idents:
            odxlinks.update(own_indent._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())
        if self.audience is not None:
            odxlinks.update(self.audience._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._flashdata = None
        if self.flashdata_ref is not None:
            self._flashdata = odxlinks.resolve(self.flashdata_ref, Flashdata)

        for odxfilter in self.filters:
            odxfilter._resolve_odxlinks(odxlinks)
        for segment in self.segments:
            segment._resolve_odxlinks(odxlinks)
        for own_indent in self.own_idents:
            own_indent._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)
        if self.audience is not None:
            self.audience._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for odxfilter in self.filters:
            odxfilter._resolve_snrefs(context)
        for segment in self.segments:
            segment._resolve_snrefs(context)
        for own_indent in self.own_idents:
            own_indent._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
        if self.audience is not None:
            self.audience._resolve_snrefs(context)
