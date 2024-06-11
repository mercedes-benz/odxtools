# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union, cast
from xml.etree import ElementTree

from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import odxassert, odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import AtomicOdxType, DataType, odxstr_to_bool
from .snrefcontext import SnRefContext

# Allowed diag-coded types
DctType = Literal[
    "LEADING-LENGTH-INFO-TYPE",
    "MIN-MAX-LENGTH-TYPE",
    "PARAM-LENGTH-INFO-TYPE",
    "STANDARD-LENGTH-TYPE",
]


@dataclass
class DiagCodedType:

    base_data_type: DataType
    base_type_encoding: Optional[str]
    is_highlow_byte_order_raw: Optional[bool]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DiagCodedType":
        base_data_type_str = odxrequire(et_element.get("BASE-DATA-TYPE"))
        try:
            base_data_type = DataType(base_data_type_str)
        except ValueError:
            odxraise(f"Unknown base data type {base_data_type_str}")
            base_data_type = cast(DataType, None)

        base_type_encoding = et_element.get("BASE-TYPE-ENCODING")
        is_highlow_byte_order_raw = odxstr_to_bool(et_element.get("IS-HIGHLOW-BYTE-ORDER"))

        return DiagCodedType(
            base_data_type=base_data_type,
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:  # noqa: B027
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:  # noqa: B027
        """Recursively resolve any odxlinks references"""
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:  # noqa: B027
        """Recursively resolve any short-name references"""
        pass

    def get_static_bit_length(self) -> Optional[int]:
        return None

    @property
    def dct_type(self) -> DctType:
        odxraise(f"Class {type(self).__name__} does not override required method "
                 f"dct_type()", NotImplementedError)
        return cast(DctType, None)

    @property
    def is_highlow_byte_order(self) -> bool:
        return self.is_highlow_byte_order_raw in [None, True]

    def _minimal_byte_length_of(self, internal_value: Union[bytes, str]) -> int:
        """Helper method to get the minimal byte length.
        (needed for LeadingLength- and MinMaxLengthType)
        """
        byte_length: int = -1
        # A_BYTEFIELD, A_ASCIISTRING, A_UNICODE2STRING, A_UTF8STRING
        if self.base_data_type == DataType.A_BYTEFIELD:
            byte_length = len(internal_value)
        elif self.base_data_type in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING]:
            if not isinstance(internal_value, str):
                odxraise()

            # TODO: Handle different encodings
            byte_length = len(bytes(internal_value, "utf-8"))
        elif self.base_data_type == DataType.A_UNICODE2STRING:
            if not isinstance(internal_value, str):
                odxraise()

            byte_length = len(bytes(internal_value, "utf-16-le"))
            odxassert(
                byte_length % 2 == 0, f"The bit length of A_UNICODE2STRING must"
                f" be a multiple of 16 but is {8*byte_length}")

        return byte_length

    def encode_into_pdu(self, internal_value: AtomicOdxType, encode_state: EncodeState) -> None:
        """Encode the internal value.

        Parameters
        ----------
        internal_value : python type corresponding to self.base_data_type
            the value to be encoded
        bit_position : int

        length_keys : Dict[OdxLinkId, int]
            mapping from ID (of the length key) to bit length
            (only needed for ParamLengthInfoType)
        """
        raise NotImplementedError(
            f".encode_into_pdu() is not implemented by the class {type(self).__name__}")

    def decode_from_pdu(self, decode_state: DecodeState) -> AtomicOdxType:
        """Decode the parameter value from the coded message.

        Parameters
        ----------
        decode_state : DecodeState
            The decoding state

        Returns
        -------
        str or int or bytes or dict
            the decoded parameter value
        int
            the next byte position after the extracted parameter
        """
        raise NotImplementedError(
            f".decode_from_pdu() is not implemented by the class {type(self).__name__}")
