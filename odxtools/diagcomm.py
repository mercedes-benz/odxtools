# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, cast
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .functionalclass import FunctionalClass
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .specialdatagroup import SpecialDataGroup
from .state import State
from .statetransition import StateTransition
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


class DiagClassType(Enum):
    STARTCOMM = "STARTCOMM"
    STOPCOMM = "STOPCOMM"
    VARIANTIDENTIFICATION = "VARIANTIDENTIFICATION"
    READ_DYN_DEFINED_MESSAGE = "READ-DYN-DEFINED-MESSAGE"
    DYN_DEF_MESSAGE = "DYN-DEF-MESSAGE"
    CLEAR_DYN_DEF_MESSAGE = "CLEAR-DYN-DEF-MESSAGE"


@dataclass
class RelatedDiagCommRef(OdxLinkRef):
    relation_type: str

    @staticmethod
    def from_et(  # type: ignore[override]
            et_element: ElementTree.Element,
            doc_frags: List[OdxDocFragment]) -> "RelatedDiagCommRef":
        kwargs = dataclass_fields_asdict(odxrequire(OdxLinkRef.from_et(et_element, doc_frags)))

        relation_type = odxrequire(et_element.findtext("RELATION-TYPE"))

        return RelatedDiagCommRef(relation_type=relation_type, **kwargs)


@dataclass
class DiagComm(IdentifiableElement):
    """Representation of a diagnostic communication object.

    Diagnostic communication objects are diagnostic services,
    single-ECU jobs and multi-ECU jobs.

    """

    admin_data: Optional[AdminData]
    sdgs: List[SpecialDataGroup]
    functional_class_refs: List[OdxLinkRef]
    audience: Optional[Audience]
    protocol_snrefs: List[str]
    related_diag_comm_refs: List[RelatedDiagCommRef]
    pre_condition_state_refs: Iterable[OdxLinkRef]
    state_transition_refs: Iterable[OdxLinkRef]

    # attributes
    semantic: Optional[str]
    diagnostic_class: Optional[DiagClassType]
    is_mandatory_raw: Optional[bool]
    is_executable_raw: Optional[bool]
    is_final_raw: Optional[bool]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagComm":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        functional_class_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF")
        ]

        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, doc_frags)

        protocol_snrefs = [
            odxrequire(el.get("SHORT-NAME"))
            for el in et_element.iterfind("PROTOCOL-SNREFS/PROTOCOL-SNREF")
        ]

        related_diag_comm_refs = [
            RelatedDiagCommRef.from_et(el, doc_frags)
            for el in et_element.iterfind("RELATED-DIAG-COMM-REFS/RELATED-DIAG-COMM-REF")
        ]

        pre_condition_state_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("PRE-CONDITION-STATE-REFS/PRE-CONDITION-STATE-REF")
        ]

        state_transition_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("STATE-TRANSITION-REFS/STATE-TRANSITION-REF")
        ]

        semantic = et_element.get("SEMANTIC")

        diagnostic_class: Optional[DiagClassType] = None
        if (diagnostic_class_str := et_element.get("DIAGNOSTIC-CLASS")) is not None:
            try:
                diagnostic_class = DiagClassType(diagnostic_class_str)
            except ValueError:
                diagnostic_class = cast(DiagClassType, None)
                odxraise(f"Encountered unknown diagnostic class type '{diagnostic_class_str}'")

        is_mandatory_raw = odxstr_to_bool(et_element.get("IS-MANDATORY"))
        is_executable_raw = odxstr_to_bool(et_element.get("IS-MANDATORY"))
        is_final_raw = odxstr_to_bool(et_element.get("IS-FINAL"))

        return DiagComm(
            admin_data=admin_data,
            sdgs=sdgs,
            functional_class_refs=functional_class_refs,
            audience=audience,
            protocol_snrefs=protocol_snrefs,
            related_diag_comm_refs=related_diag_comm_refs,
            pre_condition_state_refs=pre_condition_state_refs,
            state_transition_refs=state_transition_refs,
            semantic=semantic,
            diagnostic_class=diagnostic_class,
            is_mandatory_raw=is_mandatory_raw,
            is_executable_raw=is_executable_raw,
            is_final_raw=is_final_raw,
            **kwargs)

    @property
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        return self._functional_classes

    @property
    def protocols(self) -> NamedItemList["DiagLayer"]:
        return self._protocols

    @property
    def related_diag_comms(self) -> NamedItemList["DiagComm"]:
        return self._related_diag_comms

    @property
    def pre_condition_states(self) -> NamedItemList[State]:
        return self._pre_condition_states

    @property
    def state_transitions(self) -> NamedItemList[StateTransition]:
        return self._state_transitions

    @property
    def is_mandatory(self) -> bool:
        return self.is_mandatory_raw is True

    @property
    def is_executable(self) -> bool:
        return self.is_executable_raw in (None, True)

    @property
    def is_final(self) -> bool:
        return self.is_final_raw is True

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        if self.audience is not None:
            result.update(self.audience._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data:
            self.admin_data._resolve_odxlinks(odxlinks)

        if self.audience:
            self.audience._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        self._related_diag_comms = NamedItemList(
            [odxlinks.resolve(dc_ref, DiagComm) for dc_ref in self.related_diag_comm_refs])
        self._functional_classes = NamedItemList(
            [odxlinks.resolve(fc_ref, FunctionalClass) for fc_ref in self.functional_class_refs])
        self._pre_condition_states = NamedItemList(
            [odxlinks.resolve(st_ref, State) for st_ref in self.pre_condition_state_refs])
        self._state_transitions = NamedItemList(
            [odxlinks.resolve(stt_ref, StateTransition) for stt_ref in self.state_transition_refs])

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.admin_data:
            self.admin_data._resolve_snrefs(diag_layer)

        if self.audience:
            self.audience._resolve_snrefs(diag_layer)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

        self._protocols = NamedItemList(
            [diag_layer.protocols[prot_snref] for prot_snref in self.protocol_snrefs])
