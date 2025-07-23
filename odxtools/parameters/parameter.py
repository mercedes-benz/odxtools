# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, Literal
from xml.etree import ElementTree

from typing_extensions import final, override

from ..decodestate import DecodeState
from ..element import NamedElement
from ..encodestate import EncodeState
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkId
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


@dataclass(kw_only=True)
class Parameter(NamedElement):
    """This class corresponds to POSITIONABLE-PARAM in the ODX
    specification

    All parameter classes must adhere to the `Codec` type protocol, so
    `isinstance(param, Codec)` ought to be true.  Be aware that, even
    though the ODX specification seems to make the distinction of
    "positionable" and "normal" parameters, it does not define any
    non-positionable parameter types.

    """
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    semantic: str | None = None
    oid: str | None = None
    byte_position: int | None = None
    bit_position: int | None = None

    @property
    def parameter_type(self) -> ParameterType:
        raise NotImplementedError(
            ".parameter_type is not implemented by the concrete parameter class")

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

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Parameter":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        semantic = et_element.attrib.get("SEMANTIC")
        oid = et_element.attrib.get("OID")
        byte_position_str = et_element.findtext("BYTE-POSITION")
        byte_position = int(byte_position_str) if byte_position_str is not None else None
        bit_position_str = et_element.findtext("BIT-POSITION")
        bit_position = int(bit_position_str) if bit_position_str is not None else None

        return Parameter(
            sdgs=sdgs,
            semantic=semantic,
            oid=oid,
            byte_position=byte_position,
            bit_position=bit_position,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
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

    def get_static_bit_length(self) -> int | None:
        return None

    @final
    def encode_into_pdu(self, physical_value: ParameterValue | None,
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

    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
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
