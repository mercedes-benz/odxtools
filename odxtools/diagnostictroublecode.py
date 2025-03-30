# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import odxstr_to_bool
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .text import Text
from .utils import dataclass_fields_asdict


@dataclass
class DiagnosticTroubleCode(IdentifiableElement):
    trouble_code: int
    display_trouble_code: Optional[str]
    text: Text
    level: Optional[int]
    sdgs: List[SpecialDataGroup]

    is_temporary_raw: Optional[bool]

    @property
    def is_temporary(self) -> bool:
        return self.is_temporary_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DiagnosticTroubleCode":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        trouble_code = int(odxrequire(et_element.findtext("TROUBLE-CODE")))
        display_trouble_code = et_element.findtext("DISPLAY-TROUBLE-CODE")
        text = Text.from_et(odxrequire(et_element.find("TEXT")), doc_frags)
        level = None
        if (level_str := et_element.findtext("LEVEL")) is not None:
            level = int(level_str)
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        is_temporary_raw = odxstr_to_bool(et_element.attrib.get("IS-TEMPORARY"))

        return DiagnosticTroubleCode(
            trouble_code=trouble_code,
            text=text,
            display_trouble_code=display_trouble_code,
            level=level,
            sdgs=sdgs,
            is_temporary_raw=is_temporary_raw,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        result[self.odx_id] = self

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
