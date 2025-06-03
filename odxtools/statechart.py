# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .utils import create_description_from_et
from .odxlink import OdxLinkId, OdxDocFragment, OdxLinkDatabase
from .state import State

@dataclass
class StateChart:
    """
    Corresponds to STATE-CHART.
    """
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    semantic: Optional[str]
    states: List[State]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "StateChart":
        short_name = et_element.findtext("SHORT-NAME")
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None

        long_name = et_element.findtext("LONG-NAME")
        semantic = et_element.findtext("SEMANTIC")

        state_chart = StateChart(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            semantic=semantic,
            states=[]
        )
        states = [
            State.from_et(el, doc_frags)
            for el in et_element.iterfind("STATES/STATE")
        ]
        state_chart.states = states
        for state in states:
            state.state_chart = state_chart
        return state_chart

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return { self.odx_id: self }

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        pass
