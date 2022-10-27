# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from .parameterbase import Parameter


class TableStructParameter(Parameter):
    def __init__(self,
                 short_name,
                 table_key_ref=None,
                 table_key_snref=None,
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
            parameter_type="TABLE-STRUCT",
            semantic=semantic,
            description=description
        )
        if table_key_ref:
            self.table_key_ref = table_key_ref
        elif table_key_snref:
            self.table_key_snref = table_key_snref
        else:
            raise ValueError(
                "Either table_key_ref or table_key_snref must be defined.")

    def is_required(self):
        raise NotImplementedError(
            "TableStructParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "TableStructParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a TableStructParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a TableStructParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a TableStructParameter is not implemented yet.")
