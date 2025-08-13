# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .dtcconnector import DtcConnector
from .element import IdentifiableElement
from .envdataconnector import EnvDataConnector
from .functiondiagcommconnector import FunctionDiagCommConnector
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .tablerowconnector import TableRowConnector
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class DiagObjectConnector(IdentifiableElement):
    function_diag_comm_connectors: list[FunctionDiagCommConnector] = field(default_factory=list)
    table_row_connectors: NamedItemList[TableRowConnector] = field(default_factory=NamedItemList)
    env_data_connectors: NamedItemList[EnvDataConnector] = field(default_factory=NamedItemList)
    dtc_connectors: NamedItemList[DtcConnector] = field(default_factory=NamedItemList)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DiagObjectConnector":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        function_diag_comm_connectors = [
            FunctionDiagCommConnector.from_et(el, context) for el in et_element.iterfind(
                "FUNCTION-DIAG-COMM-CONNECTORS/FUNCTION-DIAG-COMM-CONNECTOR")
        ]
        table_row_connectors = NamedItemList([
            TableRowConnector.from_et(el, context)
            for el in et_element.iterfind("TABLE-ROW-CONNECTORS/TABLE-ROW-CONNECTOR")
        ])
        env_data_connectors = NamedItemList([
            EnvDataConnector.from_et(el, context)
            for el in et_element.iterfind("ENV-DATA-CONNECTORS/ENV-DATA-CONNECTOR")
        ])
        dtc_connectors = NamedItemList([
            DtcConnector.from_et(el, context)
            for el in et_element.iterfind("DTC-CONNECTORS/DTC-CONNECTOR")
        ])

        return DiagObjectConnector(
            function_diag_comm_connectors=function_diag_comm_connectors,
            table_row_connectors=table_row_connectors,
            env_data_connectors=env_data_connectors,
            dtc_connectors=dtc_connectors,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for fdcc in self.function_diag_comm_connectors:
            result.update(fdcc._build_odxlinks())
        for trc in self.table_row_connectors:
            result.update(trc._build_odxlinks())
        for edc in self.env_data_connectors:
            result.update(edc._build_odxlinks())
        for dtcc in self.dtc_connectors:
            result.update(dtcc._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for fdcc in self.function_diag_comm_connectors:
            fdcc._resolve_odxlinks(odxlinks)
        for trc in self.table_row_connectors:
            trc._resolve_odxlinks(odxlinks)
        for edc in self.env_data_connectors:
            edc._resolve_odxlinks(odxlinks)
        for dtcc in self.dtc_connectors:
            dtcc._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for fdcc in self.function_diag_comm_connectors:
            fdcc._resolve_snrefs(context)
        for trc in self.table_row_connectors:
            trc._resolve_snrefs(context)
        for edc in self.env_data_connectors:
            edc._resolve_snrefs(context)
        for dtcc in self.dtc_connectors:
            dtcc._resolve_snrefs(context)
