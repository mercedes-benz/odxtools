# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext
from .table import Table
from .tablerow import TableRow
from .utils import dataclass_fields_asdict


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
                doc_frags: list[OdxDocFragment]) -> "TableRowConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        table_ref = odxrequire(OdxLinkRef.from_et(et_element.find("TABLE-REF"), doc_frags))
        table_row_snref_el = odxrequire(et_element.find("TABLE-ROW-SNREF"))
        table_row_snref = odxrequire(table_row_snref_el.get("SHORT-NAME"))

        return TableRowConnector(table_ref=table_ref, table_row_snref=table_row_snref, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._table = odxlinks.resolve(self.table_ref, Table)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._table_row = resolve_snref(self.table_row_snref, self._table.table_rows, TableRow)
