# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .state import State
from .statetransition import StateTransition
from .utils import create_description_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class StateChart:
    """
    Corresponds to STATE-CHART.
    """

    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    semantic: str
    state_transitions: List[StateTransition]
    start_state_snref: str
    states: List[State]

    @property
    def start_state(self) -> State:
        return self._start_state

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "StateChart":
        short_name = et_element.findtext("SHORT-NAME")
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None

        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        semantic = et_element.findtext("SEMANTIC")
        assert semantic is not None

        state_transitions = [
            StateTransition.from_et(st_elem, doc_frags)
            for st_elem in et_element.iterfind("STATE-TRANSITIONS/STATE-TRANSITION")
        ]

        start_state_snref_elem = et_element.find("START-STATE-SNREF")
        assert start_state_snref_elem is not None
        start_state_snref = start_state_snref_elem.attrib["SHORT-NAME"]

        states = [
            State.from_et(st_elem, doc_frags) for st_elem in et_element.iterfind("STATES/STATE")
        ]

        return StateChart(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            semantic=semantic,
            state_transitions=state_transitions,
            start_state_snref=start_state_snref,
            states=states)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for st in self.states:
            odxlinks.update(st._build_odxlinks())

        for strans in self.state_transitions:
            odxlinks.update(strans._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for st in self.states:
            st._resolve_odxlinks(odxlinks)

        # For now, we assume that the start state short name ref
        # points to a state local to the state chart. TODO: The XML
        # allows to define state charts without any states, yet the
        # start state SNREF is mandatory. Is this a gap in the spec or
        # does it allow "foreign" start states? If the latter, what
        # does that mean?
        self._start_state: State
        for st in self.states:
            if st.short_name == self.start_state_snref:
                self._start_state = st
                break

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for st in self.states:
            st._resolve_snrefs(diag_layer)

        for strans in self.state_transitions:
            # note that the signature of the state transition's
            # _resolve_snrefs() method is non-standard as the
            # namespace of these SNREFs is the state chart, not the
            # whole diag layer...
            strans._resolve_snrefs(diag_layer, states=self.states)
