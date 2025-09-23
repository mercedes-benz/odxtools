# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from ..comparamspec import ComparamSpec
from ..exceptions import odxassert
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkRef
from ..parentref import ParentRef
from ..protstack import ProtStack
from .hierarchyelement import HierarchyElement
from .protocolraw import ProtocolRaw


@dataclass(kw_only=True)
class Protocol(HierarchyElement):
    """This is the class for primitives that are common for a given communication protocol

    Most importantly this diagnostic layer is responsible for defining
    the communication parameters that ought to be used.
    """

    @property
    def protocol_raw(self) -> ProtocolRaw:
        return cast(ProtocolRaw, self.diag_layer_raw)

    @property
    def comparam_spec_ref(self) -> OdxLinkRef:
        return self.protocol_raw.comparam_spec_ref

    @property
    def comparam_spec(self) -> ComparamSpec:
        return self.protocol_raw.comparam_spec

    @property
    def prot_stack_snref(self) -> str | None:
        return self.protocol_raw.prot_stack_snref

    @property
    def prot_stack(self) -> ProtStack | None:
        return self.protocol_raw.prot_stack

    @property
    def parent_refs(self) -> list[ParentRef]:
        return self.protocol_raw.parent_refs

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Protocol":
        protocol_raw = ProtocolRaw.from_et(et_element, context)

        return Protocol(diag_layer_raw=protocol_raw)

    def __post_init__(self) -> None:
        super().__post_init__()

        odxassert(
            isinstance(self.diag_layer_raw, ProtocolRaw),
            "The raw diagnostic layer passed to Protocol "
            "must be a ProtocolRaw")
