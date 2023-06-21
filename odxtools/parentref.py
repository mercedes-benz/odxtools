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


@dataclass
class ParentRef:
    layer_ref: OdxLinkRef
    not_inherited_diag_comms: List[str]  # short_name references
    not_inherited_variables: List[str]  # short_name references
    not_inherited_dops: List[str]  # short_name references
    not_inherited_tables: List[str]  # short_name references
    not_inherited_global_neg_responses: List[str]  # short_name references

    @property
    def layer(self) -> "DiagLayer":
        return self._layer

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "ParentRef":

        layer_ref = OdxLinkRef.from_et(et_element, doc_frags)
        assert layer_ref is not None

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

        return ParentRef(
            layer_ref=layer_ref,
            not_inherited_diag_comms=not_inherited_diag_comms,
            not_inherited_variables=not_inherited_variables,
            not_inherited_dops=not_inherited_dops,
            not_inherited_tables=not_inherited_tables,
            not_inherited_global_neg_responses=not_inherited_global_neg_responses,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._layer = odxlinks.resolve(self.layer_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
