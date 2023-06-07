# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from typing import TYPE_CHECKING, Any

from ..odxlink import OdxLinkDatabase
from .parameterbase import Parameter

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


class TableKeyParameter(Parameter):

    def __init__(self, *, odx_id, table_ref, table_snref, table_row_snref, table_row_ref, **kwargs):
        super().__init__(parameter_type="TABLE-KEY", **kwargs)
        self.odx_id = odx_id
        self.table_ref = table_ref
        self.table_row_ref = table_row_ref
        self.table_snref = table_snref
        self.table_row_snref = table_row_snref

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

    def _resolve_references(self, parent_dl: "DiagLayer", odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_references(parent_dl, odxlinks)
        self.table = None
        if self.table_snref:
            self.table = parent_dl.local_diag_data_dictionary_spec.tables[self.table_snref]
        if self.table_ref:
            self.table = odxlinks.resolve(self.table_ref)

        if self.table_row_ref:
            self.table_row = odxlinks.resolve(self.table_row_ref)
        if self.table_row_snref:
            self.table_row = parent_dl.local_diag_data_dictionary_spec.tables[self.table_row_snref]

        if self.table is None:
            raise ValueError("Either table_key_ref or table_key_snref must be defined.")
