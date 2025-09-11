# SPDX-License-Identifier: MIT
from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from typing_extensions import override

from ..diagvariable import DiagVariable, HasDiagVariables
from ..dyndefinedspec import DynDefinedSpec
from ..ecuvariantpattern import EcuVariantPattern
from ..exceptions import odxassert
from ..nameditemlist import NamedItemList
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkRef
from ..parentref import ParentRef
from ..variablegroup import HasVariableGroups, VariableGroup
from .basevariant import BaseVariant
from .diaglayer import DiagLayer
from .ecuvariantraw import EcuVariantRaw
from .hierarchyelement import HierarchyElement


@dataclass(kw_only=True)
class EcuVariant(HierarchyElement):

    @property
    def ecu_variant_raw(self) -> EcuVariantRaw:
        return cast(EcuVariantRaw, self.diag_layer_raw)

    @property
    def diag_variables_raw(self) -> list[DiagVariable | OdxLinkRef]:
        return self.ecu_variant_raw.diag_variables_raw

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self._diag_variables

    @property
    def variable_groups(self) -> NamedItemList[VariableGroup]:
        return self._variable_groups

    @property
    def ecu_variant_patterns(self) -> list[EcuVariantPattern]:
        return self.ecu_variant_raw.ecu_variant_patterns

    @property
    def dyn_defined_spec(self) -> DynDefinedSpec | None:
        return self.ecu_variant_raw.dyn_defined_spec

    @property
    def parent_refs(self) -> list[ParentRef]:
        return self.ecu_variant_raw.parent_refs

    @property
    def base_variant(self) -> BaseVariant | None:
        """Return the base variant for the ECU variant

        The ODX specification allows at a single base variant for each
        ECU variant, cf checker rule 50 of appendix B.2 of the
        specification document.

        """
        for pr in self.ecu_variant_raw.parent_refs:
            if isinstance(pr.layer, BaseVariant):
                return pr.layer

        return None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuVariant":
        ecu_variant_raw = EcuVariantRaw.from_et(et_element, context)

        return EcuVariant(diag_layer_raw=ecu_variant_raw)

    def __post_init__(self) -> None:
        super().__post_init__()

        odxassert(
            isinstance(self.diag_layer_raw, EcuVariantRaw),
            "The raw diagnostic layer passed to EcuVariant "
            "must be a EcuVariantRaw")

    @override
    def _compute_value_inheritance(self, odxlinks: OdxLinkDatabase) -> None:
        super()._compute_value_inheritance(odxlinks)

        self._diag_variables = NamedItemList(self._compute_available_diag_variables(odxlinks))
        self._variable_groups = NamedItemList(self._compute_available_variable_groups(odxlinks))

    def _compute_available_diag_variables(self,
                                          odxlinks: OdxLinkDatabase) -> Iterable[DiagVariable]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[DiagVariable]:
            if not isinstance(dl.diag_layer_raw, HasDiagVariables):
                return []

            return dl.diag_layer_raw.diag_variables

        def not_inherited_fn(parent_ref: ParentRef) -> list[str]:
            return parent_ref.not_inherited_variables

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_variable_groups(self,
                                           odxlinks: OdxLinkDatabase) -> Iterable[VariableGroup]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[VariableGroup]:
            if not isinstance(dl.diag_layer_raw, HasVariableGroups):
                return []

            return dl.diag_layer_raw.variable_groups

        def not_inherited_fn(parent_ref: ParentRef) -> list[str]:
            return []

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)
