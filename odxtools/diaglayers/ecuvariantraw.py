# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from ..diagvariable import DiagVariable
from ..dyndefinedspec import DynDefinedSpec
from ..ecuvariantpattern import EcuVariantPattern
from ..exceptions import odxraise
from ..nameditemlist import NamedItemList
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..parentref import ParentRef
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from ..variablegroup import VariableGroup
from .hierarchyelementraw import HierarchyElementRaw


@dataclass(kw_only=True)
class EcuVariantRaw(HierarchyElementRaw):
    diag_variables_raw: list[DiagVariable | OdxLinkRef] = field(default_factory=list)
    variable_groups: NamedItemList[VariableGroup] = field(default_factory=NamedItemList)
    ecu_variant_patterns: list[EcuVariantPattern] = field(default_factory=list)
    dyn_defined_spec: DynDefinedSpec | None = None
    parent_refs: list[ParentRef] = field(default_factory=list)

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self._diag_variables

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuVariantRaw":
        # objects contained by diagnostic layers exibit an additional
        # document fragment for the diag layer, so we use the document
        # fragments of the odx id of the diag layer for IDs of
        # contained objects.
        her = HierarchyElementRaw.from_et(et_element, context)
        kwargs = dataclass_fields_asdict(her)

        diag_variables_raw: list[DiagVariable | OdxLinkRef] = []
        if (dv_elems := et_element.find("DIAG-VARIABLES")) is not None:
            for dv_proxy_elem in dv_elems:
                dv_proxy: OdxLinkRef | DiagVariable
                if dv_proxy_elem.tag == "DIAG-VARIABLE-REF":
                    dv_proxy = OdxLinkRef.from_et(dv_proxy_elem, context)
                elif dv_proxy_elem.tag == "DIAG-VARIABLE":
                    dv_proxy = DiagVariable.from_et(dv_proxy_elem, context)
                else:
                    odxraise()

                diag_variables_raw.append(dv_proxy)

        variable_groups = NamedItemList([
            VariableGroup.from_et(vg_elem, context)
            for vg_elem in et_element.iterfind("VARIABLE-GROUPS/VARIABLE-GROUP")
        ])

        ecu_variant_patterns = None
        ecu_variant_patterns = [
            EcuVariantPattern.from_et(varpat_elem, context)
            for varpat_elem in et_element.iterfind("ECU-VARIANT-PATTERNS/ECU-VARIANT-PATTERN")
        ]

        dyn_defined_spec = None
        if (dds_elem := et_element.find("DYN-DEFINED-SPEC")) is not None:
            dyn_defined_spec = DynDefinedSpec.from_et(dds_elem, context)

        parent_refs = [
            ParentRef.from_et(pr_el, context)
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

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
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
