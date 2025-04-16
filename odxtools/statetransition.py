# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .externalaccessmethod import ExternalAccessMethod
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, resolve_snref
from .snrefcontext import SnRefContext
from .state import State
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class StateTransition(IdentifiableElement):
    """
    Corresponds to STATE-TRANSITION.
    """
    source_snref: str
    target_snref: str
    external_access_method: ExternalAccessMethod | None = None

    @property
    def source_state(self) -> State:
        return self._source_state

    @property
    def target_state(self) -> State:
        return self._target_state

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "StateTransition":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        source_snref_elem = odxrequire(et_element.find("SOURCE-SNREF"))
        source_snref = odxrequire(source_snref_elem.attrib["SHORT-NAME"])

        target_snref_elem = odxrequire(et_element.find("TARGET-SNREF"))
        target_snref = odxrequire(target_snref_elem.attrib["SHORT-NAME"])

        external_access_method = None
        if (eam_elem := et_element.find("EXTERNAL-ACCESS-METHOD")) is not None:
            external_access_method = ExternalAccessMethod.from_et(eam_elem, context)
        return StateTransition(
            source_snref=source_snref,
            target_snref=target_snref,
            external_access_method=external_access_method,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        states = odxrequire(context.state_chart).states
        self._source_state = resolve_snref(self.source_snref, states, State)
        self._target_state = resolve_snref(self.target_snref, states, State)
