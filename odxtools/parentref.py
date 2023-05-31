# SPDX-License-Identifier: MIT
import warnings
from typing import TYPE_CHECKING, Dict, List, Union

from .dataobjectproperty import DopBase
from .diaglayertype import DiagLayerType
from .exceptions import OdxWarning
from .globals import xsi
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .service import DiagService
from .singleecujob import SingleEcuJob

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

# Defines priority of overriding objects
PRIORITY_OF_DIAG_LAYER_TYPE: Dict[DiagLayerType, int] = {
    DiagLayerType.PROTOCOL:
        1,
    DiagLayerType.FUNCTIONAL_GROUP:
        2,
    DiagLayerType.BASE_VARIANT:
        3,
    DiagLayerType.ECU_VARIANT:
        4,
    # Inherited services from ECU Shared Data always override inherited services from other diag layers
    DiagLayerType.ECU_SHARED_DATA:
        5,
}


class ParentRef:

    def __init__(
        self,
        *,
        parent: Union[OdxLinkRef, "DiagLayer"],
        ref_type: str,
        not_inherited_diag_comms: List[str],  # short_name references
        not_inherited_dops: List[str],
    ):  # short_name references
        """
        Parameters
        ----------
        parent: OdxLinkRef | DiagLayer
            A reference to the or the parent DiagLayer
        ref_type: str
        not_inherited_diag_comms: List[str]
            short names of not inherited diag comms
        not_inherited_dops: List[str]
            short names of not inherited DOPs
        """
        if ref_type not in [
                "PROTOCOL-REF",
                "BASE-VARIANT-REF",
                "ECU-SHARED-DATA-REF",
                "FUNCTIONAL-GROUP-REF",
        ]:
            warnings.warn(f"Unknown parent ref type {ref_type}", OdxWarning)
        if isinstance(parent, OdxLinkRef):
            self.parent_ref = parent
            self.parent_diag_layer = None
        else:
            assert isinstance(parent, DiagLayer)

            self.parent_ref = OdxLinkRef.from_id(parent.odx_id)
            self.parent_diag_layer = parent
        self.not_inherited_diag_comms = not_inherited_diag_comms
        self.not_inherited_dops = not_inherited_dops
        self.ref_type = ref_type

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "ParentRef":

        parent_ref = OdxLinkRef.from_et(et_element, doc_frags)
        assert parent_ref is not None

        not_inherited_diag_comms = [
            el.get("SHORT-NAME") for el in et_element.iterfind(
                "NOT-INHERITED-DIAG-COMMS/NOT-INHERITED-DIAG-COMM/DIAG-COMM-SNREF")
        ]
        not_inherited_dops = [
            el.get("SHORT-NAME")
            for el in et_element.iterfind("NOT-INHERITED-DOPS/NOT-INHERITED-DOP/DOP-BASE-SNREF")
        ]
        ref_type = et_element.get(f"{xsi}type")

        return ParentRef(
            parent=parent_ref,
            ref_type=ref_type,
            not_inherited_diag_comms=not_inherited_diag_comms,
            not_inherited_dops=not_inherited_dops,
        )

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self.parent_diag_layer = odxlinks.resolve(self.parent_ref)

    def get_inheritance_priority(self):
        return PRIORITY_OF_DIAG_LAYER_TYPE[self.parent_diag_layer.variant_type]

    def get_inherited_services(self) -> List[Union[DiagService, SingleEcuJob]]:

        if self.parent_diag_layer is None:
            return []

        services = dict()
        for service in self.parent_diag_layer._services:
            assert isinstance(service, (DiagService, SingleEcuJob))

            if service.short_name not in self.not_inherited_diag_comms:
                services[service.short_name] = service

        return list(services.values())

    def get_inherited_data_object_properties(self) -> List[DopBase]:
        if self.parent_diag_layer is None:
            return []

        dops = {
            dop.short_name: dop
            for dop in self.parent_diag_layer._data_object_properties
            if dop.short_name not in self.not_inherited_dops
        }
        return list(dops.values())

    def get_inherited_communication_parameters(self):
        return self.parent_diag_layer._communication_parameters
