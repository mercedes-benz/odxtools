# SPDX-License-Identifier: MIT
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayers.diaglayer import DiagLayer


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
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "ParentRef":

        layer_ref = odxrequire(OdxLinkRef.from_et(et_element, doc_frags))

        not_inherited_diag_comms = [
            odxrequire(el.get("SHORT-NAME"))
            for el in et_element.iterfind("NOT-INHERITED-DIAG-COMMS/"
                                          "NOT-INHERITED-DIAG-COMM/"
                                          "DIAG-COMM-SNREF")
        ]
        not_inherited_dops = [
            odxrequire(el.get("SHORT-NAME")) for el in et_element.iterfind("NOT-INHERITED-DOPS/"
                                                                           "NOT-INHERITED-DOP/"
                                                                           "DOP-BASE-SNREF")
        ]
        not_inherited_tables = [
            odxrequire(el.get("SHORT-NAME")) for el in et_element.iterfind("NOT-INHERITED-TABLES/"
                                                                           "NOT-INHERITED-TABLE/"
                                                                           "TABLE-SNREF")
        ]
        not_inherited_variables = [
            odxrequire(el.get("SHORT-NAME"))
            for el in et_element.iterfind("NOT-INHERITED-VARIABLES/"
                                          "NOT-INHERITED-VARIABLE/"
                                          "DIAG-VARIABLE-SNREF")
        ]

        not_inherited_global_neg_responses = [
            odxrequire(el.get("SHORT-NAME"))
            for el in et_element.iterfind("NOT-INHERITED-GLOBAL-NEG-RESPONSES/"
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
        if TYPE_CHECKING:
            self._layer = odxlinks.resolve(self.layer_ref, DiagLayer)
        else:
            self._layer = odxlinks.resolve(self.layer_ref)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        fields = dataclass_fields_asdict(self)
        for name, value in fields.items():
            setattr(result, name, deepcopy(value))

        return result
