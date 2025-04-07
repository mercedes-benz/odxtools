# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .dyniddefmodeinfo import DynIdDefModeInfo
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class DynDefinedSpec:
    dyn_id_def_mode_infos: list[DynIdDefModeInfo] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DynDefinedSpec":
        dyn_id_def_mode_infos = [
            DynIdDefModeInfo.from_et(x, context)
            for x in et_element.iterfind("DYN-ID-DEF-MODE-INFOS/DYN-ID-DEF-MODE-INFO")
        ]
        return DynDefinedSpec(dyn_id_def_mode_infos=dyn_id_def_mode_infos)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result: dict[OdxLinkId, Any] = {}

        for didmi in self.dyn_id_def_mode_infos:
            result.update(didmi._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for didmi in self.dyn_id_def_mode_infos:
            didmi._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for didmi in self.dyn_id_def_mode_infos:
            didmi._resolve_snrefs(context)
