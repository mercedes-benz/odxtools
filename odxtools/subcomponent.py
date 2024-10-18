# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .diagnostictroublecode import DiagnosticTroubleCode
from .diagservice import DiagService
from .dtcdop import DtcDop
from .element import IdentifiableElement, NamedElement
from .environmentdata import EnvironmentData
from .environmentdatadescription import EnvironmentDataDescription
from .exceptions import odxraise, odxrequire
from .matchingparameter import MatchingParameter
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .table import Table
from .tablerow import TableRow
from .utils import dataclass_fields_asdict


@dataclass
class SubComponentPattern:
    matching_parameters: List[MatchingParameter]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SubComponentPattern":

        matching_parameters = [
            MatchingParameter.from_et(el, doc_frags)
            for el in et_element.iterfind("MATCHING-PARAMETERS/MATCHING-PARAMETER")
        ]

        return SubComponentPattern(matching_parameters=matching_parameters)


@dataclass
class SubComponentParamConnector(IdentifiableElement):
    diag_comm_snref: str

    # TODO: we currently only support SNREFs, not SNPATHREFs
    out_param_if_refs: List[str]
    in_param_if_refs: List[str]

    @property
    def service(self) -> DiagService:
        return self._service

    @property
    def out_param_ifs(self) -> NamedItemList[Parameter]:
        return self._out_param_ifs

    @property
    def in_param_ifs(self) -> NamedItemList[Parameter]:
        return self._in_param_ifs

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SubComponentParamConnector":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        diag_comm_snref = odxrequire(
            odxrequire(et_element.find("DIAG-COMM-SNREF")).get("SHORT-NAME"))

        out_param_if_refs = []
        for elem in et_element.find("OUT-PARAM-IF-REFS") or []:
            if elem.tag != "OUT-PARAM-IF-SNREF":
                odxraise("Currently, only SNREFS are supported for OUT-PARAM-IF-REFS")
                continue

            out_param_if_refs.append(odxrequire(elem.get("SHORT-NAME")))

        in_param_if_refs = []
        for elem in et_element.find("IN-PARAM-IF-REFS") or []:
            if elem.tag != "IN-PARAM-IF-SNREF":
                odxraise("Currently, only SNREFS are supported for IN-PARAM-IF-REFS")
                continue

            in_param_if_refs.append(odxrequire(elem.get("SHORT-NAME")))

        return SubComponentParamConnector(
            diag_comm_snref=diag_comm_snref,
            out_param_if_refs=out_param_if_refs,
            in_param_if_refs=in_param_if_refs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        service = resolve_snref(self.diag_comm_snref,
                                odxrequire(context.diag_layer).diag_comms, DiagService)
        self._service = service

        if self._service.request is not None:
            odxraise()
            return
        if not self._service.positive_responses:
            odxraise()
            return
        request = odxrequire(service.request)
        response = service.positive_responses[0]

        in_param_ifs = []
        for x in self.in_param_if_refs:
            in_param_ifs.append(resolve_snref(x, request.parameters, Parameter))

        out_param_ifs = []
        for x in self.out_param_if_refs:
            out_param_ifs.append(resolve_snref(x, response.parameters, Parameter))

        self._in_param_ifs = NamedItemList(in_param_ifs)
        self._out_param_ifs = NamedItemList(out_param_ifs)


@dataclass
class TableRowConnector(NamedElement):
    table_ref: OdxLinkRef
    table_row_snref: str

    @property
    def table(self) -> Table:
        return self._table

    @property
    def table_row(self) -> TableRow:
        return self._table_row

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "TableRowConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        table_ref = odxrequire(OdxLinkRef.from_et(et_element.find("TABLE-REF"), doc_frags))
        table_row_snref_el = odxrequire(et_element.find("TABLE-ROW-SNREF"))
        table_row_snref = odxrequire(table_row_snref_el.get("SHORT-NAME"))

        return TableRowConnector(table_ref=table_ref, table_row_snref=table_row_snref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._table = odxlinks.resolve(self.table_ref, Table)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._table_row = resolve_snref(self.table_row_snref, self._table.table_rows, TableRow)


@dataclass
class DtcConnector(NamedElement):
    dtc_dop_ref: OdxLinkRef
    dtc_snref: str

    @property
    def dtc_dop(self) -> DtcDop:
        return self._dtc_dop

    @property
    def dtc(self) -> DiagnosticTroubleCode:
        return self._dtc

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DtcConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        dtc_dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DTC-DOP-REF"), doc_frags))
        dtc_snref_el = odxrequire(et_element.find("DTC-SNREF"))
        dtc_snref = odxrequire(dtc_snref_el.get("SHORT-NAME"))

        return DtcConnector(dtc_dop_ref=dtc_dop_ref, dtc_snref=dtc_snref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dtc_dop = odxlinks.resolve(self.dtc_dop_ref, DtcDop)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._dtc = resolve_snref(self.dtc_snref, self._dtc_dop.dtcs, DiagnosticTroubleCode)


@dataclass
class EnvDataConnector(NamedElement):
    env_data_desc_ref: OdxLinkRef
    env_data_snref: str

    @property
    def env_data_desc(self) -> EnvironmentDataDescription:
        return self._env_data_desc

    @property
    def env_data(self) -> EnvironmentData:
        return self._env_data

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EnvDataConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        env_data_desc_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("ENV-DATA-DESC-REF"), doc_frags))
        env_data_snref_el = odxrequire(et_element.find("ENV-DATA-SNREF"))
        env_data_snref = odxrequire(env_data_snref_el.get("SHORT-NAME"))

        return EnvDataConnector(
            env_data_desc_ref=env_data_desc_ref, env_data_snref=env_data_snref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._env_data_desc = odxlinks.resolve(self.env_data_desc_ref, EnvironmentDataDescription)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._env_data = resolve_snref(self.env_data_snref, self._env_data_desc.env_datas,
                                       EnvironmentData)


@dataclass
class SubComponent(IdentifiableElement):
    """Sub-components describe collections of related diagnostic variables

    Note that the communication paradigm via diagnostic variables is
    somewhat uncommon. If your ECU does not define any, there's no
    need for it to define sub-components.

    """

    #sub_component_patterns: NamedItemList[SubComponentPattern]
    sub_component_param_connectors: NamedItemList[SubComponentParamConnector]
    table_row_connectors: NamedItemList[TableRowConnector]
    env_data_connectors: NamedItemList[EnvDataConnector]
    dtc_connectors: NamedItemList[DtcConnector]

    semantic: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "SubComponent":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        semantic = et_element.get("SEMANTIC")

        sub_component_param_connectors = [
            SubComponentParamConnector.from_et(el, doc_frags) for el in et_element.iterfind(
                "SUB-COMPONENT-PARAM-CONNECTORS/SUB-COMPONENT-PARAM-CONNECTOR")
        ]
        table_row_connectors = [
            TableRowConnector.from_et(el, doc_frags)
            for el in et_element.iterfind("TABLE-ROW-CONNECTORS/TABLE-ROW-CONNECTOR")
        ]
        env_data_connectors = [
            EnvDataConnector.from_et(el, doc_frags)
            for el in et_element.iterfind("ENV-DATA-CONNECTORS/ENV-DATA-CONNECTOR")
        ]
        dtc_connectors = [
            DtcConnector.from_et(el, doc_frags)
            for el in et_element.iterfind("DTC-CONNECTORS/DTC-CONNECTOR")
        ]

        return SubComponent(
            semantic=semantic,
            sub_component_param_connectors=NamedItemList(sub_component_param_connectors),
            table_row_connectors=NamedItemList(table_row_connectors),
            env_data_connectors=NamedItemList(env_data_connectors),
            dtc_connectors=NamedItemList(dtc_connectors),
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for dtc_conn in self.dtc_connectors:
            result.update(dtc_conn._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for dtc_conn in self.dtc_connectors:
            dtc_conn._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for dtc_conn in self.dtc_connectors:
            dtc_conn._resolve_snrefs(context)
