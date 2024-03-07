# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
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

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    @override
    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

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
    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        physical_value = encode_state.parameter_values.get(self.short_name, 0)

        bit_pos = self.bit_position or 0
        dop = odxrequire(super().dop,
                         f"A DOP is required for length key parameter {self.short_name}")
        return dop.convert_physical_to_bytes(physical_value, encode_state, bit_position=bit_pos)

    @override
    def encode_into_pdu(self, encode_state: EncodeState) -> bytes:
        return super().encode_into_pdu(encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        phys_val = super()._decode_positioned_from_pdu(decode_state)

        if not isinstance(phys_val, int):
            odxraise(f"The pysical type of length keys must be an integer, "
                     f"(is {type(phys_val).__name__})")
        decode_state.length_keys[self.short_name] = phys_val

        return phys_val
