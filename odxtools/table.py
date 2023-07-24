# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import abc
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

from .admindata import AdminData
from .dataobjectproperty import DataObjectProperty
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .tablerow import TableRow
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Table:
    """This class represents a TABLE."""

    odx_id: OdxLinkId
    semantic: Optional[str]
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    key_label: Optional[str]
    struct_label: Optional[str]
    admin_data: Optional[AdminData]
    key_dop_ref: Optional[OdxLinkRef]
    table_rows_raw: List[Union[TableRow, OdxLinkRef]]
    # TODO: table_diag_comm_connectors
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "Table":
        """Reads a TABLE."""
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        semantic = et_element.get("SEMANTIC")
        description = create_description_from_et(et_element.find("DESC"))
        key_label = et_element.findtext("KEY-LABEL")
        struct_label = et_element.findtext("STRUCT-LABEL")
        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        key_dop_ref = OdxLinkRef.from_et(et_element.find("KEY-DOP-REF"), doc_frags)

        table_rows_raw: List[Union[OdxLinkRef, TableRow]] = []
        for sub_elem in et_element:
            if sub_elem.tag == "TABLE-ROW":
                table_rows_raw.append(
                    TableRow.from_et(sub_elem, doc_frags, table_ref=OdxLinkRef.from_id(odx_id)))
            elif sub_elem.tag == "TABLE-ROW-REF":
                table_rows_raw.append(OdxLinkRef.from_et(sub_elem, doc_frags))

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return Table(
            odx_id=odx_id,
            semantic=semantic,
            short_name=short_name,
            long_name=long_name,
            description=description,
            key_label=key_label,
            struct_label=struct_label,
            admin_data=admin_data,
            key_dop_ref=key_dop_ref,
            table_rows_raw=table_rows_raw,
            sdgs=sdgs,
        )

    @property
    def key_dop(self) -> Optional[DataObjectProperty]:
        """The key data object property associated with this table."""
        return self._key_dop

    @property
    def table_rows(self) -> NamedItemList[TableRow]:
        """The table rows (both local and referenced) in this table."""
        return self._table_rows

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                result.update(table_row_wrapper._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._key_dop: Optional[DataObjectProperty] = None
        if self.key_dop_ref is not None:
            self._key_dop = odxlinks.resolve(self.key_dop_ref, DataObjectProperty)

        table_rows = []
        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                table_row = table_row_wrapper
                table_row._resolve_odxlinks(odxlinks)
            else:
                assert isinstance(table_row_wrapper, OdxLinkRef)
                table_row = odxlinks.resolve(table_row_wrapper, TableRow)

            table_rows.append(table_row)

        self._table_rows = NamedItemList(short_name_as_id, table_rows)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                table_row_wrapper._resolve_snrefs(diag_layer)

    def __repr__(self) -> str:
        return (f"Table('{self.short_name}', " + ", ".join(
            [f"table_rows='{self.table_rows}'", f"key_dop_ref='{self.key_dop_ref}'"]) + ")")
