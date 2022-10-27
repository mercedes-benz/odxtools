# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import List
from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..diagcodedtypes import DiagCodedType
from ..odxtypes import DataType
from ..exceptions import DecodeError, EncodeError

from .parameterbase import Parameter


class NrcConstParameter(Parameter):
    """A param of type NRC-CONST defines a set of values to be matched.

    An NRC-CONST can only be used in a negative response.
    Its encoding behaviour is similar to a VALUE parameter with a TEXTTABLE.
    However, an NRC-CONST is used for matching a response (similar to a CODED-CONST).

    See ASAM MCD-2 D (ODX), p. 77-79.
    """

    def __init__(self, short_name, diag_coded_type: DiagCodedType, coded_values: List[int], **kwargs):
        super().__init__(short_name,
                         parameter_type="NRC-CONST", **kwargs)

        self._diag_coded_type = diag_coded_type
        # TODO: Does it have to be an integer or is that just common practice?
        assert all(isinstance(coded_value, int)
                   for coded_value in coded_values)
        self.coded_values = coded_values

    @property
    def diag_coded_type(self):
        return self._diag_coded_type

    @property
    def bit_length(self):
        return self.diag_coded_type.bit_length

    @property
    def internal_data_type(self) -> DataType:
        return self.diag_coded_type.base_data_type

    def is_required(self):
        return False

    def is_optional(self):
        return False

    def get_coded_value(self):
        return self.coded_value

    def get_coded_value_as_bytes(self, encode_state: EncodeState):
        if self.short_name in encode_state.parameter_values:
            if encode_state.parameter_values[self.short_name] not in self.coded_values:
                raise EncodeError(f"The parameter '{self.short_name}' must have"
                                  f" one of the constant values {self.coded_values}")
            else:
                coded_value = encode_state.parameter_values[self.short_name]
        else:
            # If the user does not select one, just select any.
            # I think it does not matter ...
            coded_value = self.coded_values[0]

        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return self.diag_coded_type.convert_internal_to_bytes(coded_value,
                                                              encode_state,
                                                              bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState):
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            # Update byte position
            decode_state = decode_state._replace(
                next_byte_position=self.byte_position)

        # Extract coded values
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        coded_value, next_byte_position = \
            self.diag_coded_type.convert_bytes_to_internal(decode_state,
                                                           bit_position=bit_position_int)

        # Check if the coded value in the message is correct.
        if coded_value not in self.coded_values:
            raise DecodeError(
                f"Coded constant parameter does not match! "
                f"The parameter {self.short_name} expected a coded value in {self.coded_values} but got {coded_value} "
                f"at byte position {decode_state.next_byte_position} "
                f"in coded message {decode_state.coded_message.hex()}."
            )

        return coded_value, next_byte_position

    def _as_dict(self):
        d = super()._as_dict()
        if self.bit_length is not None:
            d["bit_length"] = self.bit_length
        d["coded_values"] = self.coded_values
        return d

    def __repr__(self):
        repr_str = f"CodedConstParameter(short_name='{self.short_name}', coded_values={self.coded_values}"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        repr_str += f", diag_coded_type={repr(self.diag_coded_type)}"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"

    def __str__(self):
        lines = [
            super().__str__(),
        ]
        return "\n".join(lines)

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"One of the constant internal values: {self.coded_values}"
