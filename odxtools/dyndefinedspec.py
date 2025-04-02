# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .dyniddefmodeinfo import DynIdDefModeInfo
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass
class DynDefinedSpec:
    dyn_id_def_mode_infos: list[DynIdDefModeInfo]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: list[OdxDocFragment]) -> "DynDefinedSpec":
        dyn_id_def_mode_infos = [
            DynIdDefModeInfo.from_et(x, doc_frags)
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
