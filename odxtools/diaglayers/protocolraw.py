# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from ..comparamspec import ComparamSpec
from ..exceptions import odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from ..parentref import ParentRef
from ..protstack import ProtStack
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
#from .comparaminstance import ComparamInstance
from .hierarchyelementraw import HierarchyElementRaw


@dataclass
class ProtocolRaw(HierarchyElementRaw):
    """This is the base class for diagnostic layers that describe a
    protocol which can be used to communicate with an ECU

    This class represents the data present in the XML, not the "logical" view.

    """

    comparam_spec_ref: OdxLinkRef
    prot_stack_snref: Optional[str]
    parent_refs: List[ParentRef]

    @property
    def comparam_spec(self) -> ComparamSpec:
        return self._comparam_spec

    @property
    def prot_stack(self) -> Optional[ProtStack]:
        return self._prot_stack

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "ProtocolRaw":
        # objects contained by diagnostic layers exibit an additional
        # document fragment for the diag layer, so we use the document
        # fragments of the odx id of the diag layer for IDs of
        # contained objects.
        her = HierarchyElementRaw.from_et(et_element, doc_frags)
        kwargs = dataclass_fields_asdict(her)
        doc_frags = her.odx_id.doc_fragments

        comparam_spec_ref = OdxLinkRef.from_et(
            odxrequire(et_element.find("COMPARAM-SPEC-REF")), doc_frags)

        prot_stack_snref = None
        if (prot_stack_snref_elem := et_element.find("PROT-STACK-SNREF")) is not None:
            prot_stack_snref = odxrequire(prot_stack_snref_elem.get("SHORT-NAME"))

        parent_refs = [
            ParentRef.from_et(pr_el, doc_frags)
            for pr_el in et_element.iterfind("PARENT-REFS/PARENT-REF")
        ]

        return ProtocolRaw(
            comparam_spec_ref=comparam_spec_ref,
            prot_stack_snref=prot_stack_snref,
            parent_refs=parent_refs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for parent_ref in self.parent_refs:
            result.update(parent_ref._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for parent_ref in self.parent_refs:
            parent_ref._resolve_odxlinks(odxlinks)

        self._comparam_spec = odxlinks.resolve(self.comparam_spec_ref, ComparamSpec)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        self._prot_stack = None
        if self.prot_stack_snref is not None:
            self._prot_stack = resolve_snref(self.prot_stack_snref, self._comparam_spec.prot_stacks,
                                             ProtStack)

        for parent_ref in self.parent_refs:
            parent_ref._resolve_snrefs(context)
