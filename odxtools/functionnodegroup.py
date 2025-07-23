# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .basefunctionnode import BaseFunctionNode
from .functionnode import FunctionNode
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class FunctionNodeGroup(BaseFunctionNode):
    function_node_refs: list[OdxLinkRef] = field(default_factory=list)
    function_node_groups: NamedItemList["FunctionNodeGroup"] = field(default_factory=NamedItemList)

    @property
    def function_nodes(self) -> NamedItemList[FunctionNode]:
        return self._function_nodes

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "FunctionNodeGroup":
        kwargs = dataclass_fields_asdict(BaseFunctionNode.from_et(et_element, context))

        function_node_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("FUNCTION-NODE-REFS/FUNCTION-NODE-REF")
        ]
        function_node_groups = NamedItemList([
            FunctionNodeGroup.from_et(el, context)
            for el in et_element.iterfind("FUNCTION-NODE-GROUPS/FUNCTION-NODE-GROUP")
        ])

        return FunctionNodeGroup(
            function_node_refs=function_node_refs,
            function_node_groups=function_node_groups,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for fng in self.function_node_groups:
            result.update(fng._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for fng in self.function_node_groups:
            fng._resolve_odxlinks(odxlinks)

        self._function_nodes = NamedItemList(
            [odxlinks.resolve(fn_elem, FunctionNode) for fn_elem in self.function_node_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for fng in self.function_node_groups:
            fng._resolve_snrefs(context)
