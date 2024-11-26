# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from xml.etree import ElementTree

from typing_extensions import final, override

from ..decodestate import DecodeState
from ..element import NamedElement
from ..encodestate import EncodeState
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..odxtypes import ParameterValue
from ..snrefcontext import SnRefContext
from ..specialdatagroup import SpecialDataGroup
from ..utils import dataclass_fields_asdict

ParameterType = Literal[
    "CODED-CONST",
    "DYNAMIC",
    "LENGTH-KEY",
    "MATCHING-REQUEST-PARAM",
    "NRC-CONST",
    "PHYS-CONST",
    "RESERVED",
    "SYSTEM",
    "TABLE-ENTRY",
    "TABLE-KEY",
    "TABLE-STRUCT",
    "VALUE",
]


@dataclass
class Parameter(NamedElement):
    """This class corresponds to POSITIONABLE-PARAM in the ODX
    specification

    All parameter classes must adhere to the `Codec` type protocol, so
    `isinstance(param, Codec)` ought to be true.  Be aware that, even
    though the ODX specification seems to make the distinction of
    "positionable" and "normal" parameters, it does not define any
    non-positionable parameter types.

    """
    oid: Optional[str]
    byte_position: Optional[int]
    bit_position: Optional[int]
    semantic: Optional[str]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Parameter":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        oid = et_element.get("OID")
        semantic = et_element.get("SEMANTIC")
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        byte_position_str = et_element.findtext("BYTE-POSITION")
        bit_position_str = et_element.findtext("BIT-POSITION")

        byte_position = int(byte_position_str) if byte_position_str is not None else None
        bit_position = int(bit_position_str) if bit_position_str is not None else None

        return Parameter(
            oid=oid,
            byte_position=byte_position,
            bit_position=bit_position,
            semantic=semantic,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

    @property
    def parameter_type(self) -> ParameterType:
        raise NotImplementedError(
            ".parameter_type is not implemented by the concrete parameter class")

    def get_static_bit_length(self) -> Optional[int]:
        return None

    @property
    def is_required(self) -> bool:
        """True if the parameter must be explicitly specified when
        encoding a message.

        Required parameters are always settable, and parameters which
        have a default value are settable but not required to be
        specified.

        """
        raise NotImplementedError(".is_required is not implemented by the concrete parameter class")

    @property
    def is_settable(self) -> bool:
        """True if the parameter can be specified when encoding a
        message.

        Required parameters are always settable, and parameters which
        have a default value are settable but not required to be
        specified.
        """
        raise NotImplementedError(".is_settable is not implemented by the concrete parameter class")

    @final
    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        """Convert a physical value into its encoded form and place it
        into the PDU

        Also, adapt the `encode_state` so that it points to where the
        next parameter is located (if the next parameter does not
        explicitly specify a position)

        """

        if self.byte_position is not None:
            encode_state.cursor_byte_position = encode_state.origin_byte_position + self.byte_position

        encode_state.cursor_bit_position = self.bit_position or 0

        self._encode_positioned_into_pdu(physical_value, encode_state)

        encode_state.cursor_bit_position = 0

    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        """Method which actually encodes the parameter

        Its location is managed by `Parameter`."""
        raise NotImplementedError(
            f"Required method '_encode_positioned_into_pdu()' not implemented by "
            f"child class {type(self).__name__}")

    @final
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        """Retrieve the raw data for the parameter from the PDU and
        convert it to its physical interpretation

        Also, adapt the `encode_state` so that it points to where the
        next parameter is located (if the next parameter does not
        explicitly specify a position)

        """

        if self.byte_position is not None:
            decode_state.cursor_byte_position = decode_state.origin_byte_position + self.byte_position

        decode_state.cursor_bit_position = self.bit_position or 0

        result = self._decode_positioned_from_pdu(decode_state)

        decode_state.cursor_bit_position = 0

        return result

    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        """Method which actually decodes the parameter

        Its location is managed by `Parameter`."""
        raise NotImplementedError(
            f"Required method '_decode_positioned_from_pdu()' not implemented by "
            f"child class {type(self).__name__}")
