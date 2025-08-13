# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .functionnode import FunctionNode
from .functionnodegroup import FunctionNodeGroup
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class FunctionDictionary(OdxCategory):
    function_nodes: NamedItemList[FunctionNode]
    function_node_groups: NamedItemList[FunctionNodeGroup]
    additional_audiences: NamedItemList[AdditionalAudience]

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "FunctionDictionary":

        base_obj = OdxCategory.from_et(et_element, context)
        kwargs = dataclass_fields_asdict(base_obj)

        function_nodes = NamedItemList([
            FunctionNode.from_et(el, context)
            for el in et_element.iterfind("FUNCTION-NODES/FUNCTION-NODE")
        ])
        function_node_groups = NamedItemList([
            FunctionNodeGroup.from_et(el, context)
            for el in et_element.iterfind("FUNCTION-NODE-GROUPS/FUNCTION-NODE-GROUP")
        ])
        additional_audiences = NamedItemList([
            AdditionalAudience.from_et(el, context)
            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")
        ])

        return FunctionDictionary(
            function_nodes=function_nodes,
            function_node_groups=function_node_groups,
            additional_audiences=additional_audiences,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for function_node in self.function_nodes:
            odxlinks.update(function_node._build_odxlinks())

        for function_node_group in self.function_node_groups:
            odxlinks.update(function_node_group._build_odxlinks())

        for additional_audience in self.additional_audiences:
            odxlinks.update(additional_audience._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for function_node in self.function_nodes:
            function_node._resolve_odxlinks(odxlinks)

        for function_node_group in self.function_node_groups:
            function_node_group._resolve_odxlinks(odxlinks)

        for additional_audience in self.additional_audiences:
            additional_audience._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for function_node in self.function_nodes:
            function_node._resolve_snrefs(context)

        for function_node_group in self.function_node_groups:
            function_node_group._resolve_snrefs(context)

        for additional_audience in self.additional_audiences:
            additional_audience._resolve_snrefs(context)
