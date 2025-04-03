# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Literal
from xml.etree import ElementTree

from typing_extensions import override

from .decodestate import DecodeState
from .diagcodedtype import DctType, DiagCodedType
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxtypes import AtomicOdxType, BytesTypes, DataType, odxstr_to_bool
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class StandardLengthType(DiagCodedType):

    bit_length: int
    bit_mask: int | None = None
    is_condensed_raw: bool | None = None

    @property
    def dct_type(self) -> DctType:
        return "STANDARD-LENGTH-TYPE"

    @property
    def is_condensed(self) -> bool:
        return self.is_condensed_raw is True

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "StandardLengthType":
        kwargs = dataclass_fields_asdict(DiagCodedType.from_et(et_element, context))

        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))
        bit_mask = read_hex_binary(et_element.find("BIT-MASK"))
        is_condensed_raw = odxstr_to_bool(et_element.get("IS-CONDENSED"))

        return StandardLengthType(
            bit_length=bit_length, bit_mask=bit_mask, is_condensed_raw=is_condensed_raw, **kwargs)

    def __post_init__(self) -> None:
        if self.bit_mask is not None:
            maskable_types = (DataType.A_UINT32, DataType.A_INT32, DataType.A_BYTEFIELD)
            odxassert(
                self.base_data_type in maskable_types,
                'Can not apply a bit_mask on a value of type {self.base_data_type}',
            )

    def __get_used_mask(self, internal_value: AtomicOdxType) -> bytes | None:
        """Returns a byte field where all bits that are used by the
        DiagCoded type are set and all unused ones are not set.

        If `None` is returned, all bits are used.
        """
        if self.bit_mask is None:
            return None

        endianness: Literal["little", "big"] = "big"
        if not self.is_highlow_byte_order and self.base_data_type in [
                DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64
        ]:
            # TODO (?): Technically, little endian A_UNICODE2STRING
            # objects require a byte swap for each 16 bit letter, and
            # thus also for the mask. I somehow doubt that this has
            # been anticipated by the standard, though...
            endianness = "little"

        if self.is_condensed:
            # if a condensed bitmask is specified, the number of bits
            # set to one in the bit mask are used in the PDU
            bit_sz = self.bit_mask.bit_count()
            used_mask = (1 << bit_sz) - 1

            return used_mask.to_bytes((bit_sz + 7) // 8, endianness)

        sz: int
        if isinstance(internal_value, BytesTypes):
            sz = len(bytes(internal_value))
        else:
            sz = (odxrequire(self.get_static_bit_length()) + 7) // 8

        max_value = (1 << (sz * 8)) - 1
        used_mask = self.bit_mask & max_value

        return used_mask.to_bytes(sz, endianness)

    def __apply_mask(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if self.bit_mask is None:
            return internal_value

        if self.is_condensed:
            int_value: int
            if isinstance(internal_value, BytesTypes):
                int_value = int.from_bytes(internal_value, 'big')
            elif isinstance(internal_value, int):
                int_value = internal_value
            else:
                odxraise("bit masks can only be specified for integers and byte fields")
                return None

            result = 0
            mask_bit = 0
            result_bit = 0

            while self.bit_mask >= (1 << mask_bit):
                if self.bit_mask & (1 << mask_bit):
                    result |= ((int_value & (1 << mask_bit)) >> mask_bit) << result_bit
                    result_bit += 1

                mask_bit += 1

            if isinstance(internal_value, BytesTypes):
                return result.to_bytes(len(bytes(internal_value)), 'big')

            return result

        if isinstance(internal_value, int):
            return internal_value & self.bit_mask
        if isinstance(internal_value, BytesTypes):
            int_value = int.from_bytes(internal_value, 'big')
            int_value &= self.bit_mask
            return int_value.to_bytes(len(bytes(internal_value)), 'big')

        odxraise(f'Can not apply a bit_mask on a value of type {type(internal_value)}')
        return internal_value

    def __unapply_mask(self, raw_value: AtomicOdxType) -> AtomicOdxType:
        if self.bit_mask is None:
            return raw_value
        if self.is_condensed:
            int_value: int
            if isinstance(raw_value, BytesTypes):
                int_value = int.from_bytes(raw_value, 'big')
            elif isinstance(raw_value, int):
                int_value = raw_value
            else:
                odxraise("bit masks can only be specified for integers and byte fields")
                return None

            result = 0
            mask_bit = 0
            input_bit = 0
            while self.bit_mask >= (1 << mask_bit):
                if self.bit_mask & (1 << mask_bit):
                    result |= ((int_value & (1 << input_bit)) >> input_bit) << mask_bit
                    input_bit += 1

                mask_bit += 1

            if isinstance(raw_value, BytesTypes):
                return result.to_bytes(len(bytes(raw_value)), 'big')

            return result
        if isinstance(raw_value, int):
            return raw_value & self.bit_mask
        if isinstance(raw_value, BytesTypes):
            int_value = int.from_bytes(raw_value, 'big')
            int_value &= self.bit_mask
            return int_value.to_bytes(len(bytes(raw_value)), 'big')

        odxraise(f'Can not apply a bit_mask on a value of type {type(raw_value)}')
        return raw_value

    def get_static_bit_length(self) -> int | None:
        if self.bit_mask is not None and self.is_condensed:
            return self.bit_mask.bit_count()

        return self.bit_length

    @override
    def encode_into_pdu(self, internal_value: AtomicOdxType, encode_state: EncodeState) -> None:
        encode_state.emplace_atomic_value(
            internal_value=self.__apply_mask(internal_value),
            used_mask=self.__get_used_mask(internal_value),
            bit_length=self.bit_length,
            base_data_type=self.base_data_type,
            base_type_encoding=self.base_type_encoding,
            is_highlow_byte_order=self.is_highlow_byte_order)

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        raw_value = decode_state.extract_atomic_value(
            bit_length=self.bit_length,
            base_data_type=self.base_data_type,
            base_type_encoding=self.base_type_encoding,
            is_highlow_byte_order=self.is_highlow_byte_order)
        internal_value = self.__unapply_mask(raw_value)

        return internal_value
