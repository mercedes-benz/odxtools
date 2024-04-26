# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from typing_extensions import override

from ..createanydiagcodedtype import create_any_diag_coded_type_from_et
from ..decodestate import DecodeState
from ..diagcodedtype import DiagCodedType
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError, odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType, DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class NrcConstParameter(Parameter):
    """A param of type NRC-CONST defines a set of values to be matched for a negative response to apply.

    The behaviour of NRC-CONST parameters is similar to CODED-CONST
    parameters in that they allow to specify which coding objects
    apply to a binary string, but in contrast to CODED-CONST
    parameters they allow to specify multiple values. Thus, the value
    of a CODED-CONST parameter is usually set using an overlapping
    VALUE parameter. Since NRC-CONST parameters can only be specified
    for negative responses, they can thus be regarded as a multiplexer
    mechanism that is specific to negative responses.

    See ASAM MCD-2 D (ODX), p. 77-79.

    """

    diag_coded_type: DiagCodedType
    coded_values: List[AtomicOdxType]

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "NrcConstParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        dct_elem = odxrequire(et_element.find("DIAG-CODED-TYPE"))
        diag_coded_type = create_any_diag_coded_type_from_et(dct_elem, doc_frags)
        coded_values = [
            diag_coded_type.base_data_type.from_string(odxrequire(val.text))
            for val in et_element.iterfind("CODED-VALUES/CODED-VALUE")
        ]

        return NrcConstParameter(
            diag_coded_type=diag_coded_type, coded_values=coded_values, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "NRC-CONST"

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result.update(self.diag_coded_type._build_odxlinks())

        return result

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    @override
    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

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
        coded_value: ParameterValue
        if physical_value is not None:
            if physical_value not in self.coded_values:
                odxraise(
                    f"The value of parameter '{self.short_name}' must "
                    f" be one of {self.coded_values} (is: {physical_value!r})", EncodeError)
                coded_value = self.coded_values[0]
            else:
                coded_value = physical_value
        else:
            # If the user did not select a value, the value of the
            # this parameter is set by another parameter which
            # overlaps with it. We thus just move the cursor.
            bit_pos = encode_state.cursor_bit_position
            bit_len = self.diag_coded_type.get_static_bit_length()

            if bit_len is None:
                odxraise("The diag coded type of NRC-CONST parameters must "
                         "exhibit a static size")
                return

            encode_state.cursor_byte_position += (bit_pos + bit_len + 7) // 8
            encode_state.cursor_bit_position = 0
            return

        self.diag_coded_type.encode_into_pdu(cast(AtomicOdxType, coded_value), encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        # Extract coded values
        coded_value = self.diag_coded_type.decode_from_pdu(decode_state)

        # Check if the coded value in the message is correct.
        if coded_value not in self.coded_values:
            warnings.warn(
                f"Coded constant parameter does not match! "
                f"The parameter {self.short_name} expected a coded "
                f"value in {str(self.coded_values)} but got {str(coded_value)} "
                f"at byte position {decode_state.cursor_byte_position} "
                f"in coded message {decode_state.coded_message.hex()}.",
                DecodeError,
                stacklevel=1,
            )

        return coded_value

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"One of the constant internal values: {self.coded_values}"
