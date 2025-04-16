# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class SpecialData:
    """This corresponds to the SD XML tag"""
    semantic_info: str | None = None  # the "SI" attribute
    text_identifier: str | None = None  # the "TI" attribute, specifies the language used
    value: str

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SpecialData":
        semantic_info = et_element.get("SI")
        text_identifier = et_element.get("TI")
        value = et_element.text or ""

        return SpecialData(
            semantic_info=semantic_info, text_identifier=text_identifier, value=value)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
