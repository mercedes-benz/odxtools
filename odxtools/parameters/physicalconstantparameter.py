# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import DecodeError

from .parameterwithdop import ParameterWithDOP


class PhysicalConstantParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 physical_constant_value,
                 **kwargs):
        super().__init__(short_name, parameter_type="PHYS-CONST",
                         **kwargs)
        assert physical_constant_value is not None
        self._physical_constant_value = physical_constant_value

    @property
    def physical_constant_value(self):
        # Cast to physical type
        return self.dop.physical_type.base_data_type.from_string(self._physical_constant_value)

    def is_required(self):
        return False

    def is_optional(self):
        return False

    def get_coded_value(self):
        return self.dop.convert_physical_to_internal(self.physical_constant_value)

    def get_coded_value_as_bytes(self, encode_state: EncodeState):
        assert self.dop is not None, "Reference to DOP is not resolved"
        if self.short_name in encode_state.parameter_values \
                and encode_state.parameter_values[self.short_name] != self.physical_constant_value:
            raise TypeError(f"The parameter '{self.short_name}' is constant {self.physical_constant_value}"
                            " and thus can not be changed.")

        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return self.dop.convert_physical_to_bytes(self.physical_constant_value,
                                                  encode_state,
                                                  bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState):
        # Decode value
        phys_val, next_byte_position = super().decode_from_pdu(decode_state)

        # Check if decoded value matches expected value
        if phys_val != self.physical_constant_value:
            raise DecodeError(
                f"Physical constant parameter does not match! "
                f"The parameter {self.short_name} expected physical value {self.physical_constant_value!r} but got {phys_val!r} "
                f"at byte position {next_byte_position} "
                f"in coded message {decode_state.coded_message.hex()}."
            )
        return phys_val, next_byte_position

    def __repr__(self) -> str:
        repr_str = f"PhysicalConstantParameter(short_name='{self.short_name}', physical_constant_value={self.physical_constant_value}"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.dop_ref is not None:
            repr_str += f", dop_ref={repr(self.dop_ref)}"
        elif self.dop_snref is not None:
            repr_str += f", dop_snref={repr(self.dop_snref)}"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"
