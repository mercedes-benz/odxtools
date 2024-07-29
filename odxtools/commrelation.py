# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .description import Description
from .diagcomm import DiagComm
from .diagservice import DiagService
from .exceptions import OdxWarning, odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext


class CommRelationValueType(Enum):
    CURRENT = "CURRENT"
    STORED = "STORED"
    STATIC = "STATIC"
    SUBSTITUTED = "SUBSTITUTED"


@dataclass
class CommRelation:
    description: Optional[Description]
    relation_type: str
    diag_comm_ref: Optional[OdxLinkRef]
    diag_comm_snref: Optional[str]
    in_param_if_snref: Optional[str]
    #in_param_if_snpathref: Optional[str] # TODO
    out_param_if_snref: Optional[str]
    #out_param_if_snpathref: Optional[str] # TODO
    value_type_raw: Optional[CommRelationValueType]

    @property
    def diag_comm(self) -> DiagComm:
        return self._diag_comm

    @property
    def in_param_if(self) -> Optional[Parameter]:
        return self._in_param_if

    @property
    def out_param_if(self) -> Optional[Parameter]:
        return self._out_param_if

    @property
    def value_type(self) -> CommRelationValueType:
        if self.value_type_raw is None:
            return CommRelationValueType.CURRENT

        return self.value_type_raw

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "CommRelation":
        description = Description.from_et(et_element.find("DESC"), doc_frags)
        relation_type = odxrequire(et_element.findtext("RELATION-TYPE"))

        diag_comm_ref = OdxLinkRef.from_et(et_element.find("DIAG-COMM-REF"), doc_frags)
        diag_comm_snref = None
        if (diag_comm_snref_elem := et_element.find("DIAG-COMM-SNREF")) is not None:
            diag_comm_snref = odxrequire(diag_comm_snref_elem.get("SHORT-NAME"))

        in_param_if_snref = None
        if (in_param_if_snref_elem := et_element.find("IN-PARAM-IF-SNREF")) is not None:
            in_param_if_snref = odxrequire(in_param_if_snref_elem.get("SHORT-NAME"))

        if et_element.find("IN-PARAM-IF-SNPATHREF") is not None:
            warnings.warn("SNPATHREFs are not supported by odxtools yet", OdxWarning, stacklevel=1)

        out_param_if_snref = None
        if (out_param_if_snref_elem := et_element.find("OUT-PARAM-IF-SNREF")) is not None:
            out_param_if_snref = odxrequire(out_param_if_snref_elem.get("SHORT-NAME"))

        if et_element.find("OUT-PARAM-IF-SNPATHREF") is not None:
            warnings.warn("SNPATHREFs are not supported by odxtools yet", OdxWarning, stacklevel=1)

        value_type_raw = None
        if (value_type_str := et_element.get("VALUE-TYPE")) is not None:
            try:
                value_type_raw = CommRelationValueType(value_type_str)
            except ValueError:
                odxraise(f"Encountered unknown comm relation value type '{value_type_str}'")

        return CommRelation(
            description=description,
            relation_type=relation_type,
            diag_comm_ref=diag_comm_ref,
            diag_comm_snref=diag_comm_snref,
            in_param_if_snref=in_param_if_snref,
            out_param_if_snref=out_param_if_snref,
            value_type_raw=value_type_raw)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.diag_comm_ref is not None:
            self._diag_comm = odxlinks.resolve(self.diag_comm_ref, DiagComm)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        diag_layer = odxrequire(context.diag_layer)

        if self.diag_comm_snref is not None:
            self._diag_comm = resolve_snref(self.diag_comm_snref, diag_layer.diag_comms, DiagComm)

        service = self.diag_comm
        if not isinstance(service, DiagService):
            odxraise(f"DIAG-VARIABLE references non-service {type(service).__name__} "
                     f"diagnostic communication")

        self._in_param_if = None
        if self.in_param_if_snref is not None:
            self._in_param_if = resolve_snref(self.in_param_if_snref,
                                              odxrequire(service.request).parameters, Parameter)

        self._out_param_if = None
        if self.out_param_if_snref is not None:
            self._out_param_if = resolve_snref(self.out_param_if_snref,
                                               odxrequire(service.positive_responses[0]).parameters,
                                               Parameter)
