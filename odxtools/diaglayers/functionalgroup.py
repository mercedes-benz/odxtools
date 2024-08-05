# SPDX-License-Identifier: MIT
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Union, cast
from xml.etree import ElementTree

from typing_extensions import override

from ..diagvariable import DiagVariable
from ..exceptions import odxassert
from ..nameditemlist import NamedItemList
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkRef
from ..parentref import ParentRef
from ..variablegroup import VariableGroup
from .diaglayer import DiagLayer
from .functionalgroupraw import FunctionalGroupRaw
from .hierarchyelement import HierarchyElement


@dataclass
class FunctionalGroup(HierarchyElement):
    """This is a diagnostic layer for functionality shared between multiple ECU variants
    """

    @property
    def functional_group_raw(self) -> FunctionalGroupRaw:
        return cast(FunctionalGroupRaw, self.diag_layer_raw)

    @property
    def diag_variables_raw(self) -> List[Union[DiagVariable, OdxLinkRef]]:
        return self.functional_group_raw.diag_variables_raw

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self._diag_variables

    @property
    def variable_groups(self) -> NamedItemList[VariableGroup]:
        return self._variable_groups

    @property
    def parent_refs(self) -> List[ParentRef]:
        return self.functional_group_raw.parent_refs

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "FunctionalGroup":
        functional_group_raw = FunctionalGroupRaw.from_et(et_element, doc_frags)

        return FunctionalGroup(diag_layer_raw=functional_group_raw)

    def __post_init__(self) -> None:
        super().__post_init__()

        odxassert(
            isinstance(self.diag_layer_raw, FunctionalGroupRaw),
            "The raw diagnostic layer passed to FunctionalGroup "
            "must be a FunctionalGroupRaw")

    @override
    def _compute_value_inheritance(self, odxlinks: OdxLinkDatabase) -> None:
        super()._compute_value_inheritance(odxlinks)

        self._diag_variables = NamedItemList(self._compute_available_diag_variables(odxlinks))
        self._variable_groups = NamedItemList(self._compute_available_variable_groups(odxlinks))

    def _compute_available_diag_variables(self,
                                          odxlinks: OdxLinkDatabase) -> Iterable[DiagVariable]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[DiagVariable]:
            if not hasattr(dl.diag_layer_raw, "diag_variables"):
                return []

            return dl.diag_layer_raw.diag_variables  # type: ignore[no-any-return]

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return parent_ref.not_inherited_variables

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_variable_groups(self,
                                           odxlinks: OdxLinkDatabase) -> Iterable[VariableGroup]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[VariableGroup]:
            if not hasattr(dl.diag_layer_raw, "variable_groups"):
                return []

            return dl.diag_layer_raw.variable_groups  # type: ignore[no-any-return]

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return []

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        """Create a deep copy of the functional group layer

        Note that the copied diagnostic layer is not fully
        initialized, so `_finalize_init()` should to be called on it
        before it can be used normally.
        """

        result = super().__deepcopy__(memo)

        # note that the self.functional_group_raw object is *not* copied at
        # this place because the attribute points to the same object
        # as self.diag_layer_raw.
        result.functional_group_raw = deepcopy(self.functional_group_raw, memo)

        return result
