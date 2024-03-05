# SPDX-License-Identifier: MIT
import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from typing_extensions import final

from ..decodestate import DecodeState
from ..element import NamedElement
from ..encodestate import EncodeState
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import ParameterValue
from ..specialdatagroup import SpecialDataGroup

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer

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
class Parameter(NamedElement, abc.ABC):
    """This class corresponds to POSITIONABLE-PARAM in the ODX
    specification.

    Be aware that, even though the ODX specification seems to make the
    distinction of "positionable" and "normal" parameters, it does not
    define any non-positionable parameter types.

    """
    byte_position: Optional[int]
    bit_position: Optional[int]
    semantic: Optional[str]
    sdgs: List[SpecialDataGroup]

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

    @property
    @abc.abstractmethod
    def parameter_type(self) -> ParameterType:
        pass

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
        raise NotImplementedError

    @property
    def is_settable(self) -> bool:
        """True if the parameter can be specified when encoding a
        message.

        Required parameters are always settable, and parameters which
        have a default value are settable but not required to be
        specified.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        """Get the coded value of the parameter given the encode state.
        Note that this method is called by `encode_into_pdu`.
        """
        pass

    @final
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        orig_cursor = decode_state.cursor_byte_position
        if self.byte_position is not None:
            decode_state.cursor_byte_position = decode_state.origin_byte_position + self.byte_position

        decode_state.cursor_bit_position = self.bit_position or 0

        result = self._decode_positioned_from_pdu(decode_state)

        decode_state.cursor_byte_position = max(decode_state.cursor_byte_position, orig_cursor)
        decode_state.cursor_bit_position = 0

        return result

    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        """Method which actually decodes the parameter

        Its location is managed by `Parameter`."""
        raise NotImplementedError(
            "Required method '_decode_positioned_from_pdu()' not implemented by child class")

    def encode_into_pdu(self, encode_state: EncodeState) -> bytes:
        """Encode the value of a parameter into a binary blob and return it

        If the byte position of the parameter is not defined,
        the byte code is appended to the blob.

        Technical note for subclasses: The default implementation
        tries to compute the coded value via
        `self.get_coded_value_as_bytes(encoded_state)` and inserts it
        into the PDU. Thus it usually suffices to overwrite
        `get_coded_value_as_bytes()` instead of `encode_into_pdu()`.

        Parameters:
        ----------
        encode_state: EncodeState, i.e. a named tuple with attributes
            * coded_message: bytes, the message encoded so far
            * parameter_values: List[ParameterValuePairs]
            * triggering_coded_request: bytes

        Returns:
        -------
        bytes
            the message's blob after adding the encoded parameter into it

        """
        msg_blob = encode_state.coded_message
        param_blob = self.get_coded_value_as_bytes(encode_state)

        if self.byte_position is not None:
            byte_position = self.byte_position
        else:
            byte_position = len(msg_blob)

        encode_state.emplace_atomic_value(param_blob, self.short_name, byte_position)

        return encode_state.coded_message
