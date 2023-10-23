# SPDX-License-Identifier: MIT
import warnings
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from ..decodestate import DecodeState
from ..diagcodedtype import DiagCodedType
from ..encodestate import EncodeState
from ..exceptions import DecodeError
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType, DataType
from .parameter import Parameter, ParameterType

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class CodedConstParameter(Parameter):

    diag_coded_type: DiagCodedType
    coded_value: AtomicOdxType

    @property
    def parameter_type(self) -> ParameterType:
        return "CODED-CONST"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result.update(self.diag_coded_type._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

    def get_static_bit_length(self) -> Optional[int]:
        return self.diag_coded_type.get_static_bit_length()

    @property
    def internal_data_type(self) -> DataType:
        return self.diag_coded_type.base_data_type

    @property
    def is_required(self) -> bool:
        return False

    @property
    def is_settable(self) -> bool:
        return False

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        if (self.short_name in encode_state.parameter_values and
                encode_state.parameter_values[self.short_name] != self.coded_value):
            raise TypeError(f"The parameter '{self.short_name}' is constant {self._coded_value_str}"
                            " and thus can not be changed.")
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return self.diag_coded_type.convert_internal_to_bytes(
            self.coded_value, encode_state=encode_state, bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[AtomicOdxType, int]:
        decode_state = copy(decode_state)
        if self.byte_position is not None and self.byte_position != decode_state.cursor_position:
            # Update byte position
            decode_state.cursor_position = self.byte_position

        # Extract coded values
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        coded_val, cursor_position = self.diag_coded_type.convert_bytes_to_internal(
            decode_state, bit_position=bit_position_int)

        # Check if the coded value in the message is correct.
        if self.coded_value != coded_val:
            warnings.warn(
                f"Coded constant parameter does not match! "
                f"The parameter {self.short_name} expected coded "
                f"value {str(self._coded_value_str)} but got {str(coded_val)} "
                f"at byte position {decode_state.cursor_position} "
                f"in coded message {decode_state.coded_message.hex()}.",
                DecodeError,
                stacklevel=1,
            )

        return coded_val, cursor_position

    @property
    def _coded_value_str(self) -> str:
        if isinstance(self.coded_value, bytes):
            return self.coded_value.hex()
        return str(self.coded_value)

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"Constant internal value: {self._coded_value_str}"
