# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from ..dataobjectproperty import DataObjectProperty
from ..encodestate import EncodeState

from .parameterwithdop import ParameterWithDOP


class ValueParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 physical_default_value=None,
                 dop_ref=None,
                 dop_snref=None,
                 **kwargs):
        super().__init__(short_name,
                         parameter_type="VALUE",
                         dop_ref=dop_ref,
                         dop_snref=dop_snref,
                         **kwargs)
        # _physical_default_value is a string. Conversion to actual type must happen after parsing
        self._physical_default_value = physical_default_value

    @property
    def physical_default_value(self):
        if self._physical_default_value is None:
            return None
        else:
            return self.dop.physical_type.base_data_type.from_string(self._physical_default_value)

    def is_required(self):
        return True if self.physical_default_value is None else False

    def is_optional(self):
        return True if self._physical_default_value is not None else False

    def get_coded_value(self, physical_value=None):
        if physical_value is not None:
            return self.dop.convert_physical_to_internal(physical_value)
        else:
            return self.dop.convert_physical_to_internal(self.physical_default_value)

    def get_coded_value_as_bytes(self, encode_state: EncodeState):
        physical_value = encode_state.parameter_values.get(self.short_name,
                                                           self.physical_default_value)
        if physical_value is None:
            raise TypeError(f"A value for parameter '{self.short_name}' must be specified"
                            f" as the parameter does not exhibit a default.")
        assert self.dop is not None, f"Param {self.short_name} does not have a DOP. Maybe resolving references failed?"

        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return self.dop.convert_physical_to_bytes(physical_value,
                                                  encode_state=encode_state,
                                                  bit_position=bit_position_int)

    def get_valid_physical_values(self):
        if isinstance(self.dop, DataObjectProperty):
            return self.dop.get_valid_physical_values()

    def __repr__(self):
        repr_str = f"ValueParameter(short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.physical_default_value is not None:
            repr_str += f", physical_default_value='{self.physical_default_value}'"
        if self.dop_ref is not None:
            repr_str += f", dop_ref='{self.dop_ref}'"
        if self.dop_snref is not None:
            repr_str += f", dop_snref='{self.dop_snref}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"
