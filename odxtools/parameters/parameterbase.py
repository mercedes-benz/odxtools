# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import abc
import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import OdxWarning
from ..globals import logger
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..specialdata import SpecialDataGroup

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


class Parameter(abc.ABC):

    def __init__(
        self,
        *,
        short_name: str,
        parameter_type: str,
        long_name: Optional[str],
        byte_position: Optional[int],
        bit_position: Optional[int],
        semantic: Optional[str],
        description: Optional[str],
        sdgs: List[SpecialDataGroup],
    ) -> None:
        self.short_name: str = short_name
        self.long_name: Optional[str] = long_name
        self.byte_position: Optional[int] = byte_position
        self.bit_position: Optional[int] = bit_position
        self.parameter_type: str = parameter_type
        self.semantic: Optional[str] = semantic
        self.description: Optional[str] = description
        self.sdgs = sdgs

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
    def bit_length(self) -> Optional[int]:
        return None

    @abc.abstractmethod
    def is_required(self):
        pass

    @abc.abstractmethod
    def is_optional(self):
        pass

    @abc.abstractmethod
    def get_coded_value(self):
        pass

    @abc.abstractmethod
    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        """Get the coded value of the parameter given the encode state.
        Note that this method is called by `encode_into_pdu`.
        """
        pass

    @abc.abstractmethod
    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[Any, int]:
        """Decode the parameter value from the coded message.

        If the parameter does have a byte position property, the coded bytes the parameter covers are extracted
        at this byte position and the function parameter `default_byte_position` is ignored.

        If the parameter does not have a byte position and a byte position is passed,
        the bytes are extracted at the byte position given by the argument `default_byte_position`.

        If the parameter does not have a byte position and the argument `default_byte_position` is None,
        this function throws a `DecodeError`.

        Parameters
        ----------
        decode_state : DecodeState
            The decoding state containing
            * the byte message to be decoded
            * the parameter values that are already decoded
            * the next byte position that is used iff the parameter does not specify a byte position

        Returns
        -------
        ParameterValuePair | List[ParameterValuePair]
            the decoded parameter value (the type is defined by the DOP)
        int
            the next byte position after the extracted parameter
        """
        pass

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

        return self._encode_into_blob(msg_blob, param_blob, byte_position)

    def _encode_into_blob(self, blob: bytes, new_data: bytes, pos: Optional[int] = None) -> bytes:
        if pos is None:
            pos = len(blob)

        # Make blob longer if necessary
        min_length = pos + len(new_data)

        result_blob = bytearray(blob)
        if len(blob) < min_length:
            result_blob.extend([0] * (min_length - len(blob)))

        for byte_idx_val, byte_idx_rpc in enumerate(range(pos, pos + len(new_data))):
            # insert byte value
            if result_blob[byte_idx_rpc] & new_data[byte_idx_val] != 0:
                warnings.warn(
                    f"Parameter {self.short_name} overlaps with another parameter (bytes are already set)",
                    OdxWarning,
                )
            result_blob[byte_idx_rpc] |= new_data[byte_idx_val]

        return result_blob

    def _as_dict(self):
        """
        Mostly for pretty printing purposes (specifically not for reconstructing the object)
        """
        d = {"short_name": self.short_name, "type": self.parameter_type, "semantic": self.semantic}
        if self.byte_position is not None:
            d["byte_position"] = self.byte_position
        if self.bit_position is not None:
            d["bit_position"] = self.bit_position
        return d

    def __repr__(self):
        repr_str = (
            f"Parameter(parameter_type='{self.parameter_type}', short_name='{self.short_name}'")
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position is not None:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"

    def __str__(self):
        # create list of all parameters. 'short_name' ought to be
        # first, so it needs special treatment...
        param_descs = [f"short_name='{self.short_name}'"]
        for (key, val) in self._as_dict().items():
            if key == "short_name":
                continue
            elif isinstance(val, str):
                param_descs.append(f"{key}='{val}'")
            else:
                param_descs.append(f"{key}={val}")

        return f"Parameter({', '.join(param_descs)})"
