# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from ..odxlink import OdxLinkRef
from .parameterbase import Parameter


class TableEntryParameter(Parameter):

    def __init__(self, *, target: str, table_row_ref: OdxLinkRef, **kwargs):
        super().__init__(parameter_type="TABLE-ENTRY", **kwargs)

        assert target in ["KEY", "STRUCT"]
        self.target = target
        self.table_row_ref = table_row_ref

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
