# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Tuple

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxrequire
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import ParameterValue
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class LengthKeyParameter(ParameterWithDOP):
    """Length Keys specify the bit (!) length of another parameter.

    The other parameter references the length key parameter using a ParamLengthInfoType as .diag_coded_type.

    LengthKeyParameters are decoded the same as ValueParameters.
    The main difference to ValueParameters is that a LengthKeyParameter has an `.odx_id` attribute
    and its DOP must be a simple DOP with PHYSICAL-TYPE/BASE-DATA-TYPE=DataType.A_UINT32.
    """

    odx_id: OdxLinkId

    @property
    def parameter_type(self) -> ParameterType:
        return "LENGTH-KEY"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result[self.odx_id] = self

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

    @property
    def is_required(self) -> bool:
        return False

    @property
    def is_settable(self) -> bool:
        # length keys can be explicitly set, but they do not need to
        # be because they can be implicitly determined by the length
        # of the corresponding field
        return True

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        physical_value = encode_state.parameter_values.get(self.short_name, 0)

        bit_pos = self.bit_position or 0
        dop = odxrequire(super().dop,
                         f"A DOP is required for length key parameter {self.short_name}")
        return dop.convert_physical_to_bytes(physical_value, encode_state, bit_position=bit_pos)

    def encode_into_pdu(self, encode_state: EncodeState) -> bytes:
        return super().encode_into_pdu(encode_state)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[ParameterValue, int]:
        return super().decode_from_pdu(decode_state)
