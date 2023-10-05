# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Tuple

from ..dataobjectproperty import DataObjectProperty
from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import DecodeError, odxraise, odxrequire
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import ParameterValue
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class PhysicalConstantParameter(ParameterWithDOP):

    physical_constant_value_raw: str

    @property
    def parameter_type(self) -> ParameterType:
        return "PHYS-CONST"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        dop = odxrequire(self.dop)
        if not isinstance(dop, DataObjectProperty):
            odxraise("The type of PHYS-CONST parameters must be a simple DOP")
        base_data_type = dop.physical_type.base_data_type
        self._physical_constant_value = base_data_type.from_string(self.physical_constant_value_raw)

    @property
    def physical_constant_value(self) -> ParameterValue:
        return self._physical_constant_value

    @property
    def is_required(self) -> bool:
        return False

    @property
    def is_settable(self) -> bool:
        return False

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        dop = odxrequire(self.dop, "Reference to DOP is not resolved")
        if (self.short_name in encode_state.parameter_values and
                encode_state.parameter_values[self.short_name] != self.physical_constant_value):
            raise TypeError(
                f"The parameter '{self.short_name}' is constant {self.physical_constant_value!r}"
                f" and thus can not be changed.")

        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return dop.convert_physical_to_bytes(
            self.physical_constant_value, encode_state, bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[ParameterValue, int]:
        # Decode value
        phys_val, cursor_position = super().decode_from_pdu(decode_state)

        # Check if decoded value matches expected value
        if phys_val != self.physical_constant_value:
            warnings.warn(
                f"Physical constant parameter does not match! "
                f"The parameter {self.short_name} expected physical value {self.physical_constant_value!r} but got {phys_val!r} "
                f"at byte position {cursor_position} "
                f"in coded message {decode_state.coded_message.hex()}.",
                DecodeError,
                stacklevel=1,
            )
        return phys_val, cursor_position
