# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, Union
from xml.etree import ElementTree

from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .specialdata import SpecialData
from .specialdatagroupcaption import SpecialDataGroupCaption


@dataclass(kw_only=True)
class SpecialDataGroup:
    """This corresponds to the SDG XML tag"""
    sdg_caption: SpecialDataGroupCaption | None = None
    sdg_caption_ref: OdxLinkRef | None = None
    values: list[Union["SpecialDataGroup", SpecialData]] = field(default_factory=list)
    semantic_info: str | None = None  # the "SI" attribute

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SpecialDataGroup":

        sdg_caption = None
        if caption_elem := et_element.find("SDG-CAPTION"):
            sdg_caption = SpecialDataGroupCaption.from_et(caption_elem, context)

        sdg_caption_ref = None
        if (caption_ref_elem := et_element.find("SDG-CAPTION-REF")) is not None:
            sdg_caption_ref = OdxLinkRef.from_et(caption_ref_elem, context)

        semantic_info = et_element.get("SI")

        values: list[SpecialData | SpecialDataGroup] = []
        for value_elem in et_element:
            next_entry: SpecialData | SpecialDataGroup | None = None
            if value_elem.tag == "SDG":
                next_entry = SpecialDataGroup.from_et(value_elem, context)
            elif value_elem.tag == "SD":
                next_entry = SpecialData.from_et(value_elem, context)

            if next_entry is not None:
                values.append(next_entry)

        return SpecialDataGroup(
            sdg_caption=sdg_caption,
            sdg_caption_ref=sdg_caption_ref,
            semantic_info=semantic_info,
            values=values,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        if self.sdg_caption_ref is None and self.sdg_caption is not None:
            result.update(self.sdg_caption._build_odxlinks())

        for val in self.values:
            result.update(val._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.sdg_caption_ref is not None:
            self.sdg_caption = odxlinks.resolve(self.sdg_caption_ref, SpecialDataGroupCaption)
        elif self.sdg_caption is not None:
            # resolve the ODXLINK references of the caption, but only
            # if the caption was specified by value, not by reference
            self.sdg_caption._resolve_odxlinks(odxlinks)

        for val in self.values:
            val._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # resolve the SNREFs of the caption, but only if the caption
        # was specified by value, not by reference
        if self.sdg_caption is not None and self.sdg_caption_ref is None:
            self.sdg_caption._resolve_snrefs(context)

        for val in self.values:
            val._resolve_snrefs(context)
