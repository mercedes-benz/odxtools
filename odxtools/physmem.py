# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .addrdefphyssegment import AddrdefPhysSegment
from .element import IdentifiableElement
from .globals import xsi
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .physsegment import PhysSegment
from .sizedefphyssegment import SizedefPhysSegment
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class PhysMem(IdentifiableElement):
    phys_segments: NamedItemList[PhysSegment]

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "PhysMem":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        phys_segments: NamedItemList[PhysSegment] = NamedItemList()
        for phys_segment_elem in et_element.iterfind("PHYS-SEGMENTS/PHYS-SEGMENT"):
            phys_segment_type = phys_segment_elem.attrib.get(f"{xsi}type")
            if phys_segment_type == "ADDRDEF-PHYS-SEGMENT":
                phys_segments.append(AddrdefPhysSegment.from_et(phys_segment_elem, context))
            elif phys_segment_type == "SIZEDEF-PHYS-SEGMENT":
                phys_segments.append(SizedefPhysSegment.from_et(phys_segment_elem, context))
            else:
                phys_segments.append(PhysSegment.from_et(phys_segment_elem, context))

        return PhysMem(phys_segments=phys_segments, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for phys_segment in self.phys_segments:
            odxlinks.update(phys_segment._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for phys_segment in self.phys_segments:
            phys_segment._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for phys_segment in self.phys_segments:
            phys_segment._resolve_snrefs(context)
