# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from .parameterwithdop import ParameterWithDOP


class SystemParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 sysparam,
                 dop_ref=None,
                 dop_snref=None,
                 long_name=None,
                 byte_position=None,
                 bit_position=None,
                 semantic=None,
                 description=None):
        super().__init__(short_name,
                         parameter_type="SYSTEM",
                         dop_ref=dop_ref,
                         dop_snref=dop_snref,
                         long_name=long_name,
                         byte_position=byte_position,
                         bit_position=bit_position,
                         semantic=semantic,
                         description=description)
        self.sysparam = sysparam

    def is_required(self):
        raise NotImplementedError(
            "SystemParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "SystemParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a SystemParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a SystemParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a SystemParameter is not implemented yet.")

    def __repr__(self):
        repr_str = f"SystemParameter(short_name='{self.short_name}', sysparam='{self.sysparam}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position={self.byte_position}"
        if self.bit_position is not None:
            repr_str += f", bit_position={self.bit_position}"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.dop_ref is not None:
            repr_str += f", dop_ref='{self.dop_ref}'"
        if self.dop_snref is not None:
            repr_str += f", dop_snref='{self.dop_snref}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"
