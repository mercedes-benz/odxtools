# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..dataobjectproperty import DataObjectProperty
from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError, odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..odxtypes import ParameterValue
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP


@dataclass
class PhysicalConstantParameter(ParameterWithDOP):

    physical_constant_value_raw: str

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "PhysicalConstantParameter":

        kwargs = dataclass_fields_asdict(ParameterWithDOP.from_et(et_element, doc_frags))

        physical_constant_value_raw = odxrequire(et_element.findtext("PHYS-CONSTANT-VALUE"))

        return PhysicalConstantParameter(
            physical_constant_value_raw=physical_constant_value_raw, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "PHYS-CONST"

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    @override
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        dop = odxrequire(self.dop)
        if not isinstance(dop, DataObjectProperty):
            odxraise("The type of PHYS-CONST parameters must be a simple DOP")
        base_data_type = dop.physical_type.base_data_type
        self._physical_constant_value = base_data_type.from_string(self.physical_constant_value_raw)

    @property
    def physical_constant_value(self) -> ParameterValue:
        return self._physical_constant_value

    @property
    @override
    def is_required(self) -> bool:
        return False

    @property
    @override
    def is_settable(self) -> bool:
        return False

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        if physical_value is not None and physical_value != self.physical_constant_value:
            odxraise(
                f"Value for constant parameter `{self.short_name}` name can "
                f"only be specified as {self.physical_constant_value!r} (is: {physical_value!r})",
                EncodeError)

        self.dop.encode_into_pdu(self.physical_constant_value, encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        # Decode value
        phys_val = super()._decode_positioned_from_pdu(decode_state)

        # Check if decoded value matches expected value
        if phys_val != self.physical_constant_value:
            odxraise(
                f"Physical constant parameter does not match! "
                f"The parameter {self.short_name} expected physical value "
                f"{self.physical_constant_value!r} but got {phys_val!r} "
                f"at byte position {decode_state.cursor_byte_position} "
                f"in coded message {decode_state.coded_message.hex()}.", DecodeError)

        return phys_val
