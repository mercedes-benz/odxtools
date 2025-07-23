# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, resolve_snref
from .snrefcontext import SnRefContext
from .state import State
from .statetransition import StateTransition
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class StateChart(IdentifiableElement):
    """
    Corresponds to STATE-CHART.
    """
    semantic: str
    state_transitions: list[StateTransition] = field(default_factory=list)
    start_state_snref: str
    states: NamedItemList[State] = field(default_factory=NamedItemList)

    @property
    def start_state(self) -> State:
        return self._start_state

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "StateChart":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        semantic: str = odxrequire(et_element.findtext("SEMANTIC"))

        state_transitions = [
            StateTransition.from_et(st_elem, context)
            for st_elem in et_element.iterfind("STATE-TRANSITIONS/STATE-TRANSITION")
        ]

        start_state_snref_elem = odxrequire(et_element.find("START-STATE-SNREF"))
        start_state_snref = start_state_snref_elem.attrib["SHORT-NAME"]

        states = [
            State.from_et(st_elem, context) for st_elem in et_element.iterfind("STATES/STATE")
        ]

        return StateChart(
            semantic=semantic,
            state_transitions=state_transitions,
            start_state_snref=start_state_snref,
            states=NamedItemList(states),
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for strans in self.state_transitions:
            odxlinks.update(strans._build_odxlinks())

        for st in self.states:
            odxlinks.update(st._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for strans in self.state_transitions:
            strans._resolve_odxlinks(odxlinks)

        for st in self.states:
            st._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.state_chart = self

        # For now, we assume that the start state short name reference
        # points to a local state of the state chart. TODO: The XSD
        # allows to define state charts without any states, yet the
        # start state SNREF is mandatory. Is this a gap in the spec or
        # does it allow "foreign" start states? If the latter, what
        # does that mean?
        self._start_state = resolve_snref(self.start_state_snref, self.states, State)

        for strans in self.state_transitions:
            strans._resolve_snrefs(context)

        for st in self.states:
            st._resolve_snrefs(context)

        context.state_chart = None
