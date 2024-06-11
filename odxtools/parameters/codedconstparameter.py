# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..createanydiagcodedtype import create_any_diag_coded_type_from_et
from ..decodestate import DecodeState
from ..diagcodedtype import DiagCodedType
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError, odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkId
from ..odxtypes import AtomicOdxType, DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass
class CodedConstParameter(Parameter):

    diag_coded_type: DiagCodedType
    coded_value: AtomicOdxType

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "CodedConstParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        dct_elem = odxrequire(et_element.find("DIAG-CODED-TYPE"))
        diag_coded_type = create_any_diag_coded_type_from_et(dct_elem, doc_frags)
        coded_value = diag_coded_type.base_data_type.from_string(
            odxrequire(et_element.findtext("CODED-VALUE")))

        return CodedConstParameter(
            diag_coded_type=diag_coded_type, coded_value=coded_value, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "CODED-CONST"

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result.update(self.diag_coded_type._build_odxlinks())

        return result

    @override
    def get_static_bit_length(self) -> Optional[int]:
        return self.diag_coded_type.get_static_bit_length()

    @property
    def internal_data_type(self) -> DataType:
        return self.diag_coded_type.base_data_type

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
        if physical_value is not None and physical_value != self.coded_value:
            odxraise(
                f"Value for constant parameter `{self.short_name}` name can "
                f"only be specified as {self.coded_value!r} (is: {physical_value!r})", EncodeError)

        internal_value = self.coded_value

        self.diag_coded_type.encode_into_pdu(
            internal_value=internal_value, encode_state=encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        coded_val = self.diag_coded_type.decode_from_pdu(decode_state)

        # Check if the coded value contained by the message is correct.
        if self.coded_value != coded_val:
            warnings.warn(
                f"Coded constant parameter does not match! "
                f"The parameter {self.short_name} expected coded "
                f"value {str(self._coded_value_str)} but got {str(coded_val)} "
                f"at byte position {decode_state.cursor_byte_position} "
                f"in coded message {decode_state.coded_message.hex()}.",
                DecodeError,
                stacklevel=1,
            )

        return coded_val

    @property
    def _coded_value_str(self) -> str:
        if isinstance(self.coded_value, bytes):
            return self.coded_value.hex()
        return str(self.coded_value)

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"Constant internal value: {self._coded_value_str}"
