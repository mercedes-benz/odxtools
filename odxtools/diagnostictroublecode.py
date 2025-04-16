# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .odxtypes import odxstr_to_bool
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .text import Text
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class DiagnosticTroubleCode(IdentifiableElement):
    trouble_code: int
    display_trouble_code: str | None = None
    text: Text
    level: int | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    is_temporary_raw: bool | None = None

    @property
    def is_temporary(self) -> bool:
        return self.is_temporary_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DiagnosticTroubleCode":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        trouble_code = int(odxrequire(et_element.findtext("TROUBLE-CODE")))
        display_trouble_code = et_element.findtext("DISPLAY-TROUBLE-CODE")
        text = Text.from_et(odxrequire(et_element.find("TEXT")), context)
        level = None
        if (level_str := et_element.findtext("LEVEL")) is not None:
            level = int(level_str)
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        is_temporary_raw = odxstr_to_bool(et_element.attrib.get("IS-TEMPORARY"))

        return DiagnosticTroubleCode(
            trouble_code=trouble_code,
            text=text,
            display_trouble_code=display_trouble_code,
            level=level,
            sdgs=sdgs,
            is_temporary_raw=is_temporary_raw,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result: dict[OdxLinkId, Any] = {}

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
