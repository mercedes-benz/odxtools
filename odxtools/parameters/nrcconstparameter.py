# SPDX-License-Identifier: MIT
import warnings
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

from ..decodestate import DecodeState
from ..diagcodedtype import DiagCodedType
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType, DataType
from .parameter import Parameter, ParameterType

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class NrcConstParameter(Parameter):
    """A param of type NRC-CONST defines a set of values to be matched.

    An NRC-CONST can only be used in a negative response.
    Its encoding behaviour is similar to a VALUE parameter with a TEXTTABLE.
    However, an NRC-CONST is used for matching a response (similar to a CODED-CONST).

    See ASAM MCD-2 D (ODX), p. 77-79.
    """

    diag_coded_type: DiagCodedType
    coded_values: List[AtomicOdxType]

    @property
    def parameter_type(self) -> ParameterType:
        return "NRC-CONST"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result.update(self.diag_coded_type._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

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
        return self.diag_coded_type.convert_internal_to_bytes(
            coded_value, encode_state, bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState):
        decode_state = copy(decode_state)
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            # Update byte position
            decode_state.next_byte_position = self.byte_position

        # Extract coded values
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        coded_value, next_byte_position = self.diag_coded_type.convert_bytes_to_internal(
            decode_state, bit_position=bit_position_int)

        # Check if the coded value in the message is correct.
        if coded_value not in self.coded_values:
            warnings.warn(
                f"Coded constant parameter does not match! "
                f"The parameter {self.short_name} expected a coded "
                f"value in {str(self.coded_values)} but got {str(coded_value)} "
                f"at byte position {decode_state.next_byte_position} "
                f"in coded message {decode_state.coded_message.hex()}.",
                DecodeError,
            )

        return coded_value, next_byte_position

    def _as_dict(self):
        d = super()._as_dict()
        if self.bit_length is not None:
            d["bit_length"] = self.bit_length
        d["coded_values"] = self.coded_values
        return d

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"One of the constant internal values: {self.coded_values}"
