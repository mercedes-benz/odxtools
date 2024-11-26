# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, cast
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import EncodeError, odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import AtomicOdxType, DataType
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .parameters.lengthkeyparameter import LengthKeyParameter


@dataclass
class ParamLengthInfoType(DiagCodedType):
    length_key_ref: OdxLinkRef

    @property
    def dct_type(self) -> DctType:
        return "PARAM-LENGTH-INFO-TYPE"

    @property
    def length_key(self) -> "LengthKeyParameter":
        return self._length_key

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ParamLengthInfoType":
        kwargs = dataclass_fields_asdict(DiagCodedType.from_et(et_element, doc_frags))

        length_key_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("LENGTH-KEY-REF"), doc_frags))

        return ParamLengthInfoType(length_key_ref=length_key_ref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve any odxlinks references"""
        super()._resolve_odxlinks(odxlinks)

        if TYPE_CHECKING:
            self._length_key = odxlinks.resolve(self.length_key_ref, LengthKeyParameter)
        else:
            self._length_key = odxlinks.resolve(self.length_key_ref)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        """Recursively resolve any short-name references"""
        super()._resolve_snrefs(context)

    @override
    def encode_into_pdu(self, internal_value: AtomicOdxType, encode_state: EncodeState) -> None:
        bit_length = encode_state.length_keys.get(self.length_key.short_name)

        if bit_length is None:
            # the length key is implicit, i.e., we need to set the
            # value for the length key in the encode_state based on
            # the value passed here.
            if self.base_data_type in [
                    DataType.A_BYTEFIELD,
                    DataType.A_ASCIISTRING,
                    DataType.A_UTF8STRING,
            ]:
                bit_length = 8 * len(cast(str, internal_value))
            elif self.base_data_type in [DataType.A_UNICODE2STRING]:
                bit_length = 16 * len(cast(str, internal_value))
            elif self.base_data_type in [DataType.A_INT32, DataType.A_UINT32]:
                bit_length = int(internal_value).bit_length()
                if self.base_data_type == DataType.A_INT32:
                    bit_length += 1
                # Round up
                bit_length = ((bit_length + 7) // 8) * 8
            elif self.base_data_type == DataType.A_FLOAT32:
                bit_length = 32
            elif self.base_data_type == DataType.A_FLOAT64:
                bit_length = 64
            else:
                odxraise(
                    f"Cannot determine size of an object of type "
                    f"{self.base_data_type.value}", EncodeError)
                return

            encode_state.length_keys[self.length_key.short_name] = bit_length

        encode_state.emplace_atomic_value(
            internal_value=internal_value,
            used_mask=None,
            bit_length=bit_length,
            base_data_type=self.base_data_type,
            is_highlow_byte_order=self.is_highlow_byte_order,
        )

    def decode_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        # First, we need to find a length key with matching ID.
        if self.length_key.short_name not in decode_state.length_keys:
            odxraise(f"Unspecified mandatory length key parameter "
                     f"{self.length_key.short_name}")
            decode_state.cursor_bit_position = 0
            return cast(None, AtomicOdxType)

        bit_length = decode_state.length_keys[self.length_key.short_name]
        if not isinstance(bit_length, int):
            odxraise(f"The bit length must be an integer, is {type(bit_length)}")
            bit_length = 0

        # Extract the internal value and return.
        return decode_state.extract_atomic_value(
            bit_length,
            self.base_data_type,
            self.is_highlow_byte_order,
        )
