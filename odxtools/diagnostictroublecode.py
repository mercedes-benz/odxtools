# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import odxstr_to_bool
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DiagnosticTroubleCode(IdentifiableElement):
    trouble_code: int
    text: Optional[str]
    display_trouble_code: Optional[str]
    level: Union[int, None]
    is_temporary_raw: Optional[bool]
    sdgs: List[SpecialDataGroup]

    @property
    def is_temporary(self) -> bool:
        return self.is_temporary_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DiagnosticTroubleCode":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        if et_element.find("DISPLAY-TROUBLE-CODE") is not None:
            display_trouble_code = et_element.findtext("DISPLAY-TROUBLE-CODE")
        else:
            display_trouble_code = None

        if (level_str := et_element.findtext("LEVEL")) is not None:
            level = int(level_str)
        else:
            level = None

        is_temporary_raw = odxstr_to_bool(et_element.get("IS-TEMPORARY"))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return DiagnosticTroubleCode(
            trouble_code=int(odxrequire(et_element.findtext("TROUBLE-CODE"))),
            text=et_element.findtext("TEXT"),
            display_trouble_code=display_trouble_code,
            level=level,
            is_temporary_raw=is_temporary_raw,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        if self.odx_id is not None:
            result[self.odx_id] = self

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
