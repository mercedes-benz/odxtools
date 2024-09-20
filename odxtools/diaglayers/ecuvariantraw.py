# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from ..diagvariable import DiagVariable
from ..dyndefinedspec import DynDefinedSpec
from ..ecuvariantpattern import EcuVariantPattern
from ..exceptions import odxraise
from ..nameditemlist import NamedItemList
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..parentref import ParentRef
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from ..variablegroup import VariableGroup
from .hierarchyelementraw import HierarchyElementRaw


@dataclass
class EcuVariantRaw(HierarchyElementRaw):
    diag_variables_raw: List[Union[DiagVariable, OdxLinkRef]]
    variable_groups: NamedItemList[VariableGroup]
    ecu_variant_patterns: List[EcuVariantPattern]
    dyn_defined_spec: Optional[DynDefinedSpec]
    parent_refs: List[ParentRef]

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self._diag_variables

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EcuVariantRaw":
        # objects contained by diagnostic layers exibit an additional
        # document fragment for the diag layer, so we use the document
        # fragments of the odx id of the diag layer for IDs of
        # contained objects.
        her = HierarchyElementRaw.from_et(et_element, doc_frags)
        kwargs = dataclass_fields_asdict(her)
        doc_frags = her.odx_id.doc_fragments

        diag_variables_raw: List[Union[DiagVariable, OdxLinkRef]] = []
        if (dv_elems := et_element.find("DIAG-VARIABLES")) is not None:
            for dv_proxy_elem in dv_elems:
                dv_proxy: Union[OdxLinkRef, DiagVariable]
                if dv_proxy_elem.tag == "DIAG-VARIABLE-REF":
                    dv_proxy = OdxLinkRef.from_et(dv_proxy_elem, doc_frags)
                elif dv_proxy_elem.tag == "DIAG-VARIABLE":
                    dv_proxy = DiagVariable.from_et(dv_proxy_elem, doc_frags)
                else:
                    odxraise()

                diag_variables_raw.append(dv_proxy)

        variable_groups = NamedItemList([
            VariableGroup.from_et(vg_elem, doc_frags)
            for vg_elem in et_element.iterfind("VARIABLE-GROUPS/VARIABLE-GROUP")
        ])

        ecu_variant_patterns = None
        ecu_variant_patterns = [
            EcuVariantPattern.from_et(varpat_elem, doc_frags)
            for varpat_elem in et_element.iterfind("ECU-VARIANT-PATTERNS/ECU-VARIANT-PATTERN")
        ]

        dyn_defined_spec = None
        if (dds_elem := et_element.find("DYN-DEFINED-SPEC")) is not None:
            dyn_defined_spec = DynDefinedSpec.from_et(dds_elem, doc_frags)

        parent_refs = [
            ParentRef.from_et(pr_el, doc_frags)
            for pr_el in et_element.iterfind("PARENT-REFS/PARENT-REF")
        ]

        # Create DiagLayer
        return EcuVariantRaw(
            diag_variables_raw=diag_variables_raw,
            variable_groups=variable_groups,
            ecu_variant_patterns=ecu_variant_patterns,
            dyn_defined_spec=dyn_defined_spec,
            parent_refs=parent_refs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for dv_proxy in self.diag_variables_raw:
            if not isinstance(dv_proxy, OdxLinkRef):
                result.update(dv_proxy._build_odxlinks())

        if self.dyn_defined_spec is not None:
            result.update(self.dyn_defined_spec._build_odxlinks())

        for parent_ref in self.parent_refs:
            result.update(parent_ref._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        self._diag_variables: NamedItemList[DiagVariable] = NamedItemList()
        for dv_proxy in self.diag_variables_raw:
            if isinstance(dv_proxy, OdxLinkRef):
                dv = odxlinks.resolve(dv_proxy, DiagVariable)
            else:
                dv_proxy._resolve_odxlinks(odxlinks)
                dv = dv_proxy

            self._diag_variables.append(dv)

        if self.dyn_defined_spec is not None:
            self.dyn_defined_spec._resolve_odxlinks(odxlinks)

        for parent_ref in self.parent_refs:
            parent_ref._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for dv_proxy in self.diag_variables_raw:
            if not isinstance(dv_proxy, OdxLinkRef):
                dv_proxy._resolve_snrefs(context)

        if self.dyn_defined_spec is not None:
            self.dyn_defined_spec._resolve_snrefs(context)

        for parent_ref in self.parent_refs:
            parent_ref._resolve_snrefs(context)
