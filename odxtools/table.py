# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .createsdgs import create_sdgs_from_et
from .dataobjectproperty import DataObjectProperty
from .element import IdentifiableElement
from .exceptions import odxassert
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .specialdatagroup import SpecialDataGroup
from .tablerow import TableRow
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Table(IdentifiableElement):
    """This class represents a TABLE."""
    semantic: Optional[str]
    key_label: Optional[str]
    struct_label: Optional[str]
    admin_data: Optional[AdminData]
    key_dop_ref: Optional[OdxLinkRef]
    table_rows_raw: List[Union[TableRow, OdxLinkRef]]
    # TODO: table_diag_comm_connectors
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Table":
        """Reads a TABLE."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        odx_id = kwargs["odx_id"]
        semantic = et_element.get("SEMANTIC")
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
            semantic=semantic,
            key_label=key_label,
            struct_label=struct_label,
            admin_data=admin_data,
            key_dop_ref=key_dop_ref,
            table_rows_raw=table_rows_raw,
            sdgs=sdgs,
            **kwargs)

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
                odxassert(isinstance(table_row_wrapper, OdxLinkRef))
                table_row = odxlinks.resolve(table_row_wrapper, TableRow)

            table_rows.append(table_row)

        self._table_rows = NamedItemList(table_rows)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for table_row_wrapper in self.table_rows_raw:
            if isinstance(table_row_wrapper, TableRow):
                table_row_wrapper._resolve_snrefs(diag_layer)
