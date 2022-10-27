# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .parameterbase import Parameter


class TableEntryParameter(Parameter):
    def __init__(self,
                 short_name,
                 target,
                 table_row_ref,
                 long_name=None,
                 byte_position=None,
                 bit_position=None,
                 semantic=None,
                 description=None):
        super().__init__(
            short_name=short_name,
            long_name=long_name,
            byte_position=byte_position,
            bit_position=bit_position,
            parameter_type="TABLE-ENTRY",
            semantic=semantic,
            description=description
        )
        assert target in ["KEY", "STRUCT"]
        self.target = target
        self.table_row_ref = table_row_ref

    def is_required(self):
        raise NotImplementedError(
            "TableKeyParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "TableKeyParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a TableKeyParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a TableKeyParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a TableKeyParameter is not implemented yet.")
