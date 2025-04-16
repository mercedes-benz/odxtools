# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from typing_extensions import override

from ..createanydiagcodedtype import create_any_diag_coded_type_from_et
from ..decodestate import DecodeState
from ..diagcodedtype import DiagCodedType
from ..encodestate import EncodeState
from ..exceptions import DecodeMismatch, EncodeError, odxraise, odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkId
from ..odxtypes import AtomicOdxType, DataType, ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass(kw_only=True)
class NrcConstParameter(Parameter):
    """A parameter of type NRC-CONST defines a set of values to be
    matched for a negative response object to apply

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

    coded_values_raw: list[str] = field(default_factory=list)
    diag_coded_type: DiagCodedType

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "NRC-CONST"

    @property
    @override
    def is_required(self) -> bool:
        return False

    @property
    @override
    def is_settable(self) -> bool:
        return False

    @property
    def internal_data_type(self) -> DataType:
        return self.diag_coded_type.base_data_type

    @property
    def coded_values(self) -> list[AtomicOdxType]:
        return self._coded_values

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "NrcConstParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, context))

        coded_values_raw = [
            odxrequire(x.text) for x in et_element.iterfind("CODED-VALUES/CODED-VALUE")
        ]
        dct_elem = odxrequire(et_element.find("DIAG-CODED-TYPE"))
        diag_coded_type = create_any_diag_coded_type_from_et(dct_elem, context)

        return NrcConstParameter(
            coded_values_raw=coded_values_raw, diag_coded_type=diag_coded_type, **kwargs)

    def __post_init__(self) -> None:
        self._coded_values = [
            self.diag_coded_type.base_data_type.from_string(val) for val in self.coded_values_raw
        ]

    @override
    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result.update(self.diag_coded_type._build_odxlinks())

        return result

    @override
    def get_static_bit_length(self) -> int | None:
        return self.diag_coded_type.get_static_bit_length()

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:
        # NRC-CONST parameters are not encoding any value on its
        # own. instead, it is supposed to overlap with a value
        # parameter.
        if physical_value is not None:
            odxraise("The value of NRC-CONST parameters cannot be set directly!", EncodeError)

        # TODO (?): extract the parameter and check if it is one of
        # the values of self.coded_values. if not, throw an
        # EncodeMismatch exception! This is probably a bad idea
        # because the parameter which determines the value of the
        # NRC-CONST might possibly be specified after the NRC-CONST.

        # move the cursor forward by the size of the parameter
        bit_pos = encode_state.cursor_bit_position
        bit_len = self.diag_coded_type.get_static_bit_length()

        if bit_len is None:
            odxraise("The diag coded type of NRC-CONST parameters must "
                     "exhibit a static size")
            return

        encode_state.cursor_byte_position += (bit_pos + bit_len + 7) // 8
        encode_state.cursor_bit_position = 0

        encode_state.emplace_bytes(b'', self.short_name)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        # Extract coded value
        coded_value = self.diag_coded_type.decode_from_pdu(decode_state)

        # Check if the coded value in the message is correct.
        if coded_value not in self.coded_values:
            raise DecodeMismatch(f"NRC-CONST parameter {self.short_name} does not apply")

        return coded_value

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"One of the constant internal values: {self.coded_values}"
