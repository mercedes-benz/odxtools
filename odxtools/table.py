# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .dataobjectproperty import DataObjectProperty
from .element import IdentifiableElement
from .exceptions import odxassert
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .tablediagcommconnector import TableDiagCommConnector
from .tablerow import TableRow
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class Table(IdentifiableElement):
    """This class represents a TABLE."""
    key_label: str | None = None
    struct_label: str | None = None
    admin_data: AdminData | None = None
    key_dop_ref: OdxLinkRef | None = None
    table_rows_raw: list[TableRow | OdxLinkRef] = field(default_factory=list)
    table_diag_comm_connectors: list[TableDiagCommConnector] = field(default_factory=list)
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    semantic: str | None = None

    @property
    def key_dop(self) -> DataObjectProperty | None:
        """The key data object property associated with this table."""
        return self._key_dop

    @property
    def table_rows(self) -> NamedItemList[TableRow]:
        """The table rows (both local and referenced) in this table."""
        return self._table_rows

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Table":
        """Reads a TABLE."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))
        odx_id = kwargs["odx_id"]
        key_label = et_element.findtext("KEY-LABEL")
        struct_label = et_element.findtext("STRUCT-LABEL")
        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        key_dop_ref = OdxLinkRef.from_et(et_element.find("KEY-DOP-REF"), context)

        table_rows_raw: list[OdxLinkRef | TableRow] = []
        for sub_elem in et_element:
            if sub_elem.tag == "TABLE-ROW":
                table_rows_raw.append(
                    TableRow.tablerow_from_et(
                        sub_elem, context, table_ref=OdxLinkRef.from_id(odx_id)))
            elif sub_elem.tag == "TABLE-ROW-REF":
                table_rows_raw.append(OdxLinkRef.from_et(sub_elem, context))

        table_diag_comm_connectors = [
            TableDiagCommConnector.from_et(dcc_elem, context) for dcc_elem in et_element.iterfind(
                "TABLE-DIAG-COMM-CONNECTORS/TABLE-DIAG-COMM-CONNECTOR")
        ]
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        semantic = et_element.get("SEMANTIC")

        return Table(
            key_label=key_label,
            struct_label=struct_label,
            admin_data=admin_data,
            key_dop_ref=key_dop_ref,
            table_rows_raw=table_rows_raw,
            table_diag_comm_connectors=table_diag_comm_connectors,
            sdgs=sdgs,
            semantic=semantic,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                result.update(table_row_wrapper._build_odxlinks())

        for dcc in self.table_diag_comm_connectors:
            result.update(dcc._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._key_dop: DataObjectProperty | None = None
        if self.key_dop_ref is not None:
            self._key_dop = odxlinks.resolve(self.key_dop_ref, DataObjectProperty)

        table_rows = []
        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                table_row = table_row_wrapper
                table_row._resolve_odxlinks(odxlinks)
            else:
                odxassert(isinstance(table_row_wrapper, OdxLinkRef))
                table_row = odxlinks.resolve(table_row_wrapper, TableRow)

            table_rows.append(table_row)

        self._table_rows = NamedItemList(table_rows)

        for dcc in self.table_diag_comm_connectors:
            dcc._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                table_row_wrapper._resolve_snrefs(context)

        for dcc in self.table_diag_comm_connectors:
            dcc._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
