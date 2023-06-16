# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from .parameterbase import Parameter


class TableStructParameter(Parameter):

    def __init__(self, *, table_key_ref, table_key_snref, **kwargs):
        super().__init__(parameter_type="TABLE-STRUCT", **kwargs)

        self.table_key_ref = table_key_ref
        self.table_key_snref = table_key_snref
        if self.table_key_ref is None and self.table_key_snref is None:
            raise OdxError("Either table_key_ref or table_key_snref "
                           "must be defined.")

    def is_required(self):
        raise NotImplementedError("TableStructParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError("TableStructParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError("Encoding a TableStructParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError("Encoding a TableStructParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError("Decoding a TableStructParameter is not implemented yet.")
