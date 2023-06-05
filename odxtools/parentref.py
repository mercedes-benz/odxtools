# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union

from .dataobjectproperty import DopBase
from .diaglayertype import DiagLayerType
from .globals import xsi
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .service import DiagService
from .singleecujob import SingleEcuJob

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

# Defines priority of overriding objects
PRIORITY_OF_DIAG_LAYER_TYPE: Dict[DiagLayerType, int] = {
    DiagLayerType.ECU_SHARED_DATA: 0,
    DiagLayerType.PROTOCOL: 1,
    DiagLayerType.FUNCTIONAL_GROUP: 2,
    DiagLayerType.BASE_VARIANT: 3,
    DiagLayerType.ECU_VARIANT: 4,
}


@dataclass
class ParentRef:
    parent_layer_ref: OdxLinkRef
    self_layer_type: DiagLayerType
    parent_layer_type: DiagLayerType
    not_inherited_diag_comms: List[str]  # short_name references
    not_inherited_variables: List[str]  # short_name references
    not_inherited_dops: List[str]  # short_name references
    not_inherited_tables: List[str]  # short_name references
    not_inherited_global_neg_responses: List[str]  # short_name references

    def __post_init__(self) -> None:
        # make sure that the layer from which we inherit are of lower
        # priority than us.
        self_prio = PRIORITY_OF_DIAG_LAYER_TYPE[self.self_layer_type]
        parent_prio = PRIORITY_OF_DIAG_LAYER_TYPE[self.parent_layer_type]
        assert self_prio > parent_prio, "diagnostic layers can only inherit from layers of lower priority"

    @property
    def parent_layer(self) -> "DiagLayer":
        return self._parent_layer

    @staticmethod
    def from_et(et_element, self_layer_type: DiagLayerType,
                doc_frags: List[OdxDocFragment]) -> "ParentRef":

        parent_layer_ref = OdxLinkRef.from_et(et_element, doc_frags)
        assert parent_layer_ref is not None

        not_inherited_diag_comms = [
            el.get("SHORT-NAME") for el in et_element.iterfind("NOT-INHERITED-DIAG-COMMS/"
                                                               "NOT-INHERITED-DIAG-COMM/"
                                                               "DIAG-COMM-SNREF")
        ]
        not_inherited_dops = [
            el.get("SHORT-NAME") for el in et_element.iterfind("NOT-INHERITED-DOPS/"
                                                               "NOT-INHERITED-DOP/"
                                                               "DOP-BASE-SNREF")
        ]
        not_inherited_tables = [
            el.get("SHORT-NAME") for el in et_element.iterfind("NOT-INHERITED-TABLES/"
                                                               "NOT-INHERITED-TABLE/"
                                                               "TABLE-SNREF")
        ]
        not_inherited_variables = [
            el.get("SHORT-NAME") for el in et_element.iterfind("NOT-INHERITED-VARIABLES/"
                                                               "NOT-INHERITED-VARIABLE/"
                                                               "DIAG-VARIABLE-SNREF")
        ]

        not_inherited_global_neg_responses = [
            el.get("SHORT-NAME") for el in et_element.iterfind("NOT-INHERITED-GLOBAL-NEG-RESPONSES/"
                                                               "NOT-INHERITED-GLOBAL-NEG-RESPONSE/"
                                                               "GLOBAL-NEG-RESPONSE-SNREF")
        ]

        # determine the type of the referenced diag layer. for
        # this, we need to strip the '-REF' suffix of the
        # element's {xsi}type attribute
        parent_layer_type_str = et_element.get(f"{xsi}type")
        assert parent_layer_type_str is not None and parent_layer_type_str.endswith("-REF")
        parent_layer_type = DiagLayerType(parent_layer_type_str[:-4])

        return ParentRef(
            parent_layer_ref=parent_layer_ref,
            self_layer_type=self_layer_type,
            parent_layer_type=DiagLayerType(parent_layer_type),
            not_inherited_diag_comms=not_inherited_diag_comms,
            not_inherited_variables=not_inherited_variables,
            not_inherited_dops=not_inherited_dops,
            not_inherited_tables=not_inherited_tables,
            not_inherited_global_neg_responses=not_inherited_global_neg_responses,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        self._parent_layer = odxlinks.resolve(self.parent_layer_ref)

        assert self._parent_layer.variant_type == self.parent_layer_type, \
            "Incorrect PARENT-REF"

    def get_inheritance_priority(self):
        return PRIORITY_OF_DIAG_LAYER_TYPE[self.parent_layer_type]

    def get_inherited_services(self) -> List[Union[DiagService, SingleEcuJob]]:
        if self.parent_layer is None:
            return []

        services = dict()
        for service in self.parent_layer._services:
            assert isinstance(service, (DiagService, SingleEcuJob))

            if service.short_name not in self.not_inherited_diag_comms:
                services[service.short_name] = service

        return list(services.values())

    def get_inherited_data_object_properties(self) -> List[DopBase]:
        if self.parent_layer is None:
            return []

        dops = {
            dop.short_name: dop
            for dop in self.parent_layer._data_object_properties
            if dop.short_name not in self.not_inherited_dops
        }
        return list(dops.values())

    def get_inherited_communication_parameters(self):
        return self.parent_layer._communication_parameters
