# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .specialdata import SpecialData
from .specialdatagroupcaption import SpecialDataGroupCaption


@dataclass
class SpecialDataGroup:
    sdg_caption: Optional[SpecialDataGroupCaption]
    sdg_caption_ref: Optional[OdxLinkRef]
    values: List[Union["SpecialDataGroup", SpecialData]]
    semantic_info: Optional[str]  # the "SI" attribute

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SpecialDataGroup":

        sdg_caption = None
        if caption_elem := et_element.find("SDG-CAPTION"):
            sdg_caption = SpecialDataGroupCaption.from_et(caption_elem, doc_frags)

        sdg_caption_ref = None
        if (caption_ref_elem := et_element.find("SDG-CAPTION-REF")) is not None:
            sdg_caption_ref = OdxLinkRef.from_et(caption_ref_elem, doc_frags)

        semantic_info = et_element.get("SI")

        values: List[Union[SpecialData, SpecialDataGroup]] = []
        for value_elem in et_element:
            next_entry: Optional[Union[SpecialData, SpecialDataGroup]] = None
            if value_elem.tag == "SDG":
                next_entry = SpecialDataGroup.from_et(value_elem, doc_frags)
            elif value_elem.tag == "SD":
                next_entry = SpecialData.from_et(value_elem, doc_frags)

            if next_entry is not None:
                values.append(next_entry)

        return SpecialDataGroup(
            sdg_caption=sdg_caption,
            sdg_caption_ref=sdg_caption_ref,
            semantic_info=semantic_info,
            values=values,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
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
