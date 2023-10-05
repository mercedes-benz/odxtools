# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Tuple

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import odxraise
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import AtomicOdxType, DataType

if TYPE_CHECKING:
    from .diaglayer import DiagLayer
    from .parameters.lengthkeyparameter import LengthKeyParameter


@dataclass
class ParamLengthInfoType(DiagCodedType):

    length_key_ref: OdxLinkRef

    @property
    def dct_type(self) -> DctType:
        return "PARAM-LENGTH-INFO-TYPE"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve any odxlinks references"""
        super()._resolve_odxlinks(odxlinks)

        self._length_key = odxlinks.resolve(self.length_key_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        """Recursively resolve any short-name references"""
        super()._resolve_snrefs(diag_layer)

    @property
    def length_key(self) -> "LengthKeyParameter":
        return self._length_key

    def convert_internal_to_bytes(self, internal_value: AtomicOdxType, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        bit_length = encode_state.parameter_values.get(self.length_key.short_name, None)

        if bit_length is None:
            if self.base_data_type in [
                    DataType.A_BYTEFIELD,
                    DataType.A_ASCIISTRING,
                    DataType.A_UTF8STRING,
            ]:
                bit_length = 8 * len(internal_value)  # type: ignore[arg-type]
            if self.base_data_type in [DataType.A_UNICODE2STRING]:
                bit_length = 16 * len(internal_value)  # type: ignore[arg-type]

            if self.base_data_type in [DataType.A_INT32, DataType.A_UINT32]:
                bit_length = int(internal_value).bit_length()
                if self.base_data_type == DataType.A_INT32:
                    bit_length += 1
                # Round up
                bit_length = ((bit_length + 7) // 8) * 8

            encode_state.parameter_values[self.length_key.short_name] = bit_length

        if bit_length is None:
            odxraise()

        return self._to_bytes(
            internal_value,
            bit_position=bit_position,
            bit_length=bit_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

    def convert_bytes_to_internal(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[AtomicOdxType, int]:
        # Find length key with matching ID.
        bit_length = None
        for parameter_name, value in decode_state.parameter_values.items():
            if parameter_name == self.length_key.short_name:
                # The bit length of the parameter to be extracted is given by the length key.
                bit_length = value
                if not isinstance(bit_length, int):
                    odxraise(f"The bit length must be an integer, is {type(bit_length)}")
                break

        if not isinstance(bit_length, int):
            odxraise(f"Did not find any length key with short name {self.length_key.short_name}")

        # Extract the internal value and return.
        return self._extract_internal(
            decode_state.coded_message,
            decode_state.cursor_position,
            bit_position,
            bit_length,
            self.base_data_type,
            self.is_highlow_byte_order,
        )
