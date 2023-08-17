# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .state import State
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class StateTransition(IdentifiableElement):
    """
    Corresponds to STATE-TRANSITION.
    """
    source_snref: str
    target_snref: str
    #external_access_method: Optional[ExternalAccessMethod] # TODO

    @property
    def source_state(self) -> State:
        return self._source_state

    @property
    def target_state(self) -> State:
        return self._target_state

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "StateTransition":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        source_snref_elem = odxrequire(et_element.find("SOURCE-SNREF"))
        source_snref = odxrequire(source_snref_elem.attrib["SHORT-NAME"])

        target_snref_elem = odxrequire(et_element.find("TARGET-SNREF"))
        target_snref = odxrequire(target_snref_elem.attrib["SHORT-NAME"])

        return StateTransition(source_snref=source_snref, target_snref=target_snref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    # note that the signature of this method is non-standard because
    # the namespace of these SNREFs is the corresponding state
    # chart. To mitigate this a bit, the non-standard parameters are
    # keyword-only...
    def _resolve_snrefs(self, diag_layer: "DiagLayer", *, states: Iterable[State]) -> None:
        self._source_state: State
        self._target_state: State
        for st in states:
            if st.short_name == self.source_snref:
                self._source_state = st
            if st.short_name == self.target_snref:
                self._target_state = st
