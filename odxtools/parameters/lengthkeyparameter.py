# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from typing_extensions import final, override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import EncodeError, odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkId
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP


@dataclass
class LengthKeyParameter(ParameterWithDOP):
    """Length Keys specify the bit (!) length of another parameter.

    The other parameter references the length key parameter using a ParamLengthInfoType as .diag_coded_type.

    LengthKeyParameters are decoded the same as ValueParameters.
    The main difference to ValueParameters is that a LengthKeyParameter has an `.odx_id` attribute
    and its DOP must be a simple DOP with PHYSICAL-TYPE/BASE-DATA-TYPE=DataType.A_UINT32.
    """

    odx_id: OdxLinkId

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "LengthKeyParameter":

        kwargs = dataclass_fields_asdict(ParameterWithDOP.from_et(et_element, doc_frags))

        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))

        return LengthKeyParameter(odx_id=odx_id, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "LENGTH-KEY"

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result[self.odx_id] = self

        return result

    @property
    @override
    def is_required(self) -> bool:
        return False

    @property
    @override
    def is_settable(self) -> bool:
        # length keys can be explicitly set, but they do not need to
        # be because they can be implicitly determined by the length
        # of the corresponding field
        return True

    @override
    @final
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        # if you get this exception, you ought to use
        # `.encode_placeholder_into_pdu()` followed by (after the
        # value of the length key has been determined)
        # `.encode_value_into_pdu()`.
        raise RuntimeError("_encode_positioned_into_pdu() cannot be called for length keys.")

    def encode_placeholder_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:

        if physical_value is not None:
            if not self.dop.is_valid_physical_value(physical_value):
                odxraise(f"Invalid explicitly specified physical value '{physical_value!r}' "
                         f"for length key '{self.short_name}'.")

            lkv = encode_state.length_keys.get(self.short_name)
            if lkv is not None and lkv != physical_value:
                odxraise(f"Got conflicting values for length key {self.short_name}: "
                         f"{lkv} and {physical_value!r}")

            if not isinstance(physical_value, int):
                odxraise(
                    f"Value of length key {self.short_name} is of type {type(physical_value).__name__} "
                    f"instead of int")

            encode_state.length_keys[self.short_name] = physical_value

        pos = encode_state.cursor_byte_position
        if self.byte_position is not None:
            pos = encode_state.origin_byte_position + self.byte_position
        encode_state.key_pos[self.short_name] = pos
        encode_state.cursor_byte_position = pos
        encode_state.cursor_bit_position = self.bit_position or 0

        # emplace a value of zero into the encode state, but pretend the bits not to be used
        n = odxrequire(self.dop.get_static_bit_length()) + encode_state.cursor_bit_position
        tmp_val = b'\x00' * ((n + 7) // 8)
        encode_state.emplace_bytes(tmp_val, obj_used_mask=tmp_val)

        encode_state.cursor_bit_position = 0

    def encode_value_into_pdu(self, encode_state: EncodeState) -> None:

        if self.short_name not in encode_state.length_keys:
            odxraise(
                f"Length key {self.short_name} has not been defined before "
                f"it is required.", EncodeError)
            return
        else:
            physical_value = encode_state.length_keys[self.short_name]

        encode_state.cursor_byte_position = encode_state.key_pos[self.short_name]
        encode_state.cursor_bit_position = self.bit_position or 0

        self.dop.encode_into_pdu(encode_state=encode_state, physical_value=physical_value)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        phys_val = super()._decode_positioned_from_pdu(decode_state)

        if not isinstance(phys_val, int):
            odxraise(f"The pysical type of length keys must be an integer, "
                     f"(is {type(phys_val).__name__})")
        decode_state.length_keys[self.short_name] = phys_val

        return phys_val
