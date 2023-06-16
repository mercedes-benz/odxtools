# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class SpecialDataGroupCaption:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SpecialDataGroupCaption":
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None

        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        return SpecialDataGroupCaption(
            odx_id=odx_id, short_name=short_name, long_name=long_name, description=description)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        result[self.odx_id] = self

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass


@dataclass
class SpecialData:
    semantic_info: Optional[str]  # the "SI" attribute
    text_identifier: Optional[str]  # the "TI" attribute, specifies the language used
    value: str

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "SpecialData":
        semantic_info = et_element.get("SI")
        text_identifier = et_element.get("TI")
        value = et_element.text or ""

        return SpecialData(
            semantic_info=semantic_info, text_identifier=text_identifier, value=value)


@dataclass
class SpecialDataGroup:
    sdg_caption: Optional[SpecialDataGroupCaption]
    sdg_caption_ref: Optional[OdxLinkRef]
    semantic_info: Optional[str]  # the "SI" attribute
    values: List[Union["SpecialDataGroup", SpecialData]]

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

        if self.sdg_caption is not None:
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

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        # resolve the SNREFs of the caption, but only if the caption
        # was specified by value, not by reference
        if self.sdg_caption is not None and self.sdg_caption_ref is None:
            self.sdg_caption._resolve_snrefs(diag_layer)

        for val in self.values:
            val._resolve_snrefs(diag_layer)


def create_sdgs_from_et(et_element: Optional[ElementTree.Element],
                        doc_frags: List[OdxDocFragment]) -> List[SpecialDataGroup]:

    if not et_element:
        return []

    result = []
    for sdg_elem in et_element.iterfind("SDG"):
        result.append(SpecialDataGroup.from_et(sdg_elem, doc_frags))

    return result
