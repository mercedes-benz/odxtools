# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .diagclasstype import DiagClassType
from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .functionalclass import FunctionalClass
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .odxtypes import odxstr_to_bool
from .preconditionstateref import PreConditionStateRef
from .relateddiagcommref import RelatedDiagCommRef
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .state import State
from .statetransition import StateTransition
from .statetransitionref import StateTransitionRef
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayers.protocol import Protocol


@dataclass(kw_only=True)
class DiagComm(IdentifiableElement):
    """Representation of a diagnostic communication object.

    Diagnostic communication objects are diagnostic services,
    single-ECU jobs and multi-ECU jobs.

    """

    admin_data: AdminData | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    functional_class_refs: list[OdxLinkRef] = field(default_factory=list)
    audience: Audience | None = None
    protocol_snrefs: list[str] = field(default_factory=list)
    related_diag_comm_refs: list[RelatedDiagCommRef] = field(default_factory=list)
    pre_condition_state_refs: list[PreConditionStateRef] = field(default_factory=list)
    state_transition_refs: list[StateTransitionRef] = field(default_factory=list)

    # attributes
    semantic: str | None = None
    diagnostic_class: DiagClassType | None = None
    is_mandatory_raw: bool | None = None
    is_executable_raw: bool | None = None
    is_final_raw: bool | None = None

    @property
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        return self._functional_classes

    @property
    def protocols(self) -> NamedItemList["Protocol"]:
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

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DiagComm":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        functional_class_refs = [
            odxrequire(OdxLinkRef.from_et(el, context))
            for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF")
        ]

        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, context)

        protocol_snrefs = [
            odxrequire(el.get("SHORT-NAME"))
            for el in et_element.iterfind("PROTOCOL-SNREFS/PROTOCOL-SNREF")
        ]

        related_diag_comm_refs = [
            RelatedDiagCommRef.from_et(el, context)
            for el in et_element.iterfind("RELATED-DIAG-COMM-REFS/RELATED-DIAG-COMM-REF")
        ]

        pre_condition_state_refs = [
            PreConditionStateRef.from_et(el, context)
            for el in et_element.iterfind("PRE-CONDITION-STATE-REFS/PRE-CONDITION-STATE-REF")
        ]

        state_transition_refs = [
            StateTransitionRef.from_et(el, context)
            for el in et_element.iterfind("STATE-TRANSITION-REFS/STATE-TRANSITION-REF")
        ]

        semantic = et_element.attrib.get("SEMANTIC")

        diagnostic_class: DiagClassType | None = None
        if (diagnostic_class_str := et_element.attrib.get("DIAGNOSTIC-CLASS")) is not None:
            try:
                diagnostic_class = DiagClassType(diagnostic_class_str)
            except ValueError:
                odxraise(f"Encountered unknown diagnostic class type '{diagnostic_class_str}'")

        is_mandatory_raw = odxstr_to_bool(et_element.attrib.get("IS-MANDATORY"))
        is_executable_raw = odxstr_to_bool(et_element.attrib.get("IS-EXECUTABLE"))
        is_final_raw = odxstr_to_bool(et_element.attrib.get("IS-FINAL"))

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

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        if self.audience is not None:
            result.update(self.audience._build_odxlinks())

        for pc_ref in self.pre_condition_state_refs:
            result.update(pc_ref._build_odxlinks())

        for st_ref in self.state_transition_refs:
            result.update(st_ref._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data:
            self.admin_data._resolve_odxlinks(odxlinks)

        if self.audience:
            self.audience._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        for pc_ref in self.pre_condition_state_refs:
            pc_ref._resolve_odxlinks(odxlinks)

        for st_ref in self.state_transition_refs:
            st_ref._resolve_odxlinks(odxlinks)

        self._related_diag_comms = NamedItemList(
            [odxlinks.resolve(dc_ref, DiagComm) for dc_ref in self.related_diag_comm_refs])
        self._functional_classes = NamedItemList(
            [odxlinks.resolve(fc_ref, FunctionalClass) for fc_ref in self.functional_class_refs])
        self._pre_condition_states = NamedItemList(
            [odxlinks.resolve(st_ref, State) for st_ref in self.pre_condition_state_refs])
        self._state_transitions = NamedItemList(
            [odxlinks.resolve(stt_ref, StateTransition) for stt_ref in self.state_transition_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data:
            self.admin_data._resolve_snrefs(context)

        if self.audience:
            self.audience._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

        for pc_ref in self.pre_condition_state_refs:
            pc_ref._resolve_snrefs(context)

        for st_ref in self.state_transition_refs:
            st_ref._resolve_snrefs(context)

        if TYPE_CHECKING:
            diag_layer = odxrequire(context.diag_layer)
            self._protocols = NamedItemList([
                resolve_snref(prot_snref, getattr(diag_layer, "protocols", []), Protocol)
                for prot_snref in self.protocol_snrefs
            ])
        else:
            diag_layer = odxrequire(context.diag_layer)
            self._protocols = NamedItemList([
                resolve_snref(prot_snref, getattr(diag_layer, "protocols", []))
                for prot_snref in self.protocol_snrefs
            ])
