# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List
from xml.etree import ElementTree

from ..comparaminstance import ComparamInstance
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from .diaglayerraw import DiagLayerRaw


@dataclass
class HierarchyElementRaw(DiagLayerRaw):
    """This is the base class for diagnostic layers that may be involved in value inheritance

    This class represents the data present in the XML, not the "logical" view.
    """

    comparam_refs: List[ComparamInstance]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "HierarchyElementRaw":
        # objects contained by diagnostic layers exibit an additional
        # document fragment for the diag layer, so we use the document
        # fragments of the odx id of the diag layer for IDs of
        # contained objects.
        dlr = DiagLayerRaw.from_et(et_element, doc_frags)
        kwargs = dataclass_fields_asdict(dlr)
        doc_frags = dlr.odx_id.doc_fragments

        comparam_refs = [
            ComparamInstance.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPARAM-REFS/COMPARAM-REF")
        ]

        return HierarchyElementRaw(comparam_refs=comparam_refs, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for comparam_ref in self.comparam_refs:
            result.update(comparam_ref._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for comparam_ref in self.comparam_refs:
            comparam_ref._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for comparam_ref in self.comparam_refs:
            comparam_ref._resolve_snrefs(context)
