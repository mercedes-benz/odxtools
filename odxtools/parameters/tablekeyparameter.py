# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from typing import TYPE_CHECKING, Any, Dict

from ..odxlink import OdxLinkDatabase, OdxLinkId
from .parameterbase import Parameter

if TYPE_CHECKING:
    from ..table import Table, TableRow
    from .diaglayer import DiagLayer


class TableKeyParameter(Parameter):

    def __init__(self, *, odx_id, table_ref, table_snref, table_row_snref, table_row_ref, **kwargs):
        super().__init__(parameter_type="TABLE-KEY", **kwargs)
        self.odx_id = odx_id
        self.table_ref = table_ref
        self.table_row_ref = table_row_ref
        self.table_snref = table_snref
        self.table_row_snref = table_row_snref

        if self.table_ref is None and self.table_snref is None and \
           self.table_row_ref is None and self.table_row_snref is None:
            raise ValueError("Either a table or a table row must be defined.")

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result[self.odx_id] = self

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.table_ref:
            self._table = odxlinks.resolve(self.table_ref)
        if self.table_row_ref:
            self._table_row = odxlinks.resolve(self.table_row_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        if self.table_snref:
            self._table = diag_layer.tables[self.table_snref]
        if self.table_row_snref:
            self._table_row = diag_layer.tables[self.table_row_snref]

    @property
    def table(self) -> "Table":
        return self._table

    @property
    def table_row(self) -> "TableRow":
        return self._table_row

    def is_required(self):
        raise NotImplementedError("TableKeyParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError("TableKeyParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError("Encoding a TableKeyParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError("Encoding a TableKeyParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError("Decoding a TableKeyParameter is not implemented yet.")
