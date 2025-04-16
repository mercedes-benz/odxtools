# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .dtcconnector import DtcConnector
from .element import IdentifiableElement
from .envdataconnector import EnvDataConnector
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .subcomponentparamconnector import SubComponentParamConnector
from .subcomponentpattern import SubComponentPattern
from .tablerowconnector import TableRowConnector
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SubComponent(IdentifiableElement):
    """Sub-components describe collections of related diagnostic variables

    Note that the communication paradigm via diagnostic variables is
    somewhat uncommon. If your ECU does not define any, there's no
    need for it to define sub-components.

    """

    sub_component_patterns: list[SubComponentPattern] = field(default_factory=list)
    sub_component_param_connectors: NamedItemList[SubComponentParamConnector] = field(
        default_factory=NamedItemList)
    table_row_connectors: NamedItemList[TableRowConnector] = field(default_factory=NamedItemList)
    env_data_connectors: NamedItemList[EnvDataConnector] = field(default_factory=NamedItemList)
    dtc_connectors: NamedItemList[DtcConnector] = field(default_factory=NamedItemList)

    semantic: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SubComponent":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        semantic = et_element.get("SEMANTIC")

        sub_component_patterns = [
            SubComponentPattern.from_et(el, context)
            for el in et_element.iterfind("SUB-COMPONENT-PATTERNS/SUB-COMPONENT-PATTERN")
        ]
        sub_component_param_connectors = [
            SubComponentParamConnector.from_et(el, context) for el in et_element.iterfind(
                "SUB-COMPONENT-PARAM-CONNECTORS/SUB-COMPONENT-PARAM-CONNECTOR")
        ]
        table_row_connectors = [
            TableRowConnector.from_et(el, context)
            for el in et_element.iterfind("TABLE-ROW-CONNECTORS/TABLE-ROW-CONNECTOR")
        ]
        env_data_connectors = [
            EnvDataConnector.from_et(el, context)
            for el in et_element.iterfind("ENV-DATA-CONNECTORS/ENV-DATA-CONNECTOR")
        ]
        dtc_connectors = [
            DtcConnector.from_et(el, context)
            for el in et_element.iterfind("DTC-CONNECTORS/DTC-CONNECTOR")
        ]

        return SubComponent(
            semantic=semantic,
            sub_component_patterns=sub_component_patterns,
            sub_component_param_connectors=NamedItemList(sub_component_param_connectors),
            table_row_connectors=NamedItemList(table_row_connectors),
            env_data_connectors=NamedItemList(env_data_connectors),
            dtc_connectors=NamedItemList(dtc_connectors),
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for scp in self.sub_component_patterns:
            result.update(scp._build_odxlinks())

        for scpc in self.sub_component_param_connectors:
            result.update(scpc._build_odxlinks())

        for trc in self.table_row_connectors:
            result.update(trc._build_odxlinks())

        for edc in self.env_data_connectors:
            result.update(edc._build_odxlinks())

        for dtc_conn in self.dtc_connectors:
            result.update(dtc_conn._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for scp in self.sub_component_patterns:
            scp._resolve_odxlinks(odxlinks)

        for scpc in self.sub_component_param_connectors:
            scpc._resolve_odxlinks(odxlinks)

        for trc in self.table_row_connectors:
            trc._resolve_odxlinks(odxlinks)

        for edc in self.env_data_connectors:
            edc._resolve_odxlinks(odxlinks)

        for dtc_conn in self.dtc_connectors:
            dtc_conn._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for scp in self.sub_component_patterns:
            scp._resolve_snrefs(context)

        for scpc in self.sub_component_param_connectors:
            scpc._resolve_snrefs(context)

        for trc in self.table_row_connectors:
            trc._resolve_snrefs(context)

        for edc in self.env_data_connectors:
            edc._resolve_snrefs(context)

        for dtc_conn in self.dtc_connectors:
            dtc_conn._resolve_snrefs(context)
