# SPDX-License-Identifier: MIT
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from ..comparamspec import ComparamSpec
from ..exceptions import odxassert
from ..odxlink import OdxDocFragment
from ..protstack import ProtStack
from .hierarchyelement import HierarchyElement
from .protocolraw import ProtocolRaw


@dataclass
class Protocol(HierarchyElement):
    """This is the class for primitives that are common for a given communication protocol

    Most importantly this diagnostic layer is responsible for defining
    the communication parameters that ought to be used.
    """

    @property
    def protocol_raw(self) -> ProtocolRaw:
        return cast(ProtocolRaw, self.diag_layer_raw)

    @property
    def comparam_spec(self) -> ComparamSpec:
        return self.protocol_raw.comparam_spec

    @property
    def prot_stack(self) -> Optional[ProtStack]:
        return self.protocol_raw.prot_stack

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Protocol":
        protocol_raw = ProtocolRaw.from_et(et_element, doc_frags)

        return Protocol(diag_layer_raw=protocol_raw)

    def __post_init__(self) -> None:
        super().__post_init__()

        odxassert(
            isinstance(self.diag_layer_raw, ProtocolRaw),
            "The raw diagnostic layer passed to Protocol "
            "must be a ProtocolRaw")

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        """Create a deep copy of the protocol layer

        Note that the copied diagnostic layer is not fully
        initialized, so `_finalize_init()` should to be called on it
        before it can be used normally.
        """

        result = super().__deepcopy__(memo)

        # note that the self.protocol_raw object is *not* copied at
        # this place because the attribute points to the same object
        # as self.diag_layer_raw.
        result.protocol_raw = deepcopy(self.protocol_raw, memo)

        return result
