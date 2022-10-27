# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from .parameterbase import Parameter


class DynamicParameter(Parameter):
    def __init__(self,
                 short_name,
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
            parameter_type="DYNAMIC",
            semantic=semantic,
            description=description
        )

    def is_required(self):
        raise NotImplementedError(
            "DynamicParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "DynamicParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a DynamicParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a DynamicParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a DynamicParameter is not implemented yet.")

    def __repr__(self):
        repr_str = f"DynamicParameter(short_name='{self.short_name}', sysparam='{self.sysparam}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"
