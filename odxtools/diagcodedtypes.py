# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
import math
from typing import Any, Optional, Union, List

from .odxtypes import DataType
from .exceptions import DecodeError, EncodeError
from .globals import xsi, logger
from .decodestate import DecodeState
from .encodestate import EncodeState
from .odxlink import OdxLinkId, OdxDocFragment

import bitstruct

ODX_TYPE_TO_FORMAT_LETTER = {
    DataType.A_INT32: 's',
    DataType.A_UINT32: 'u',
    DataType.A_FLOAT32: 'f',
    DataType.A_FLOAT64: 'f',
    DataType.A_BYTEFIELD: 'r',
    DataType.A_UNICODE2STRING: 'r',  # UTF-16 strings must be converted explicitly
    DataType.A_ASCIISTRING: 't',
    DataType.A_UTF8STRING: 't'
}


class DiagCodedType(abc.ABC):
    def __init__(self,
                 base_data_type: Union[str, DataType],
                 dct_type: str,
                 base_type_encoding=None,
                 is_highlow_byte_order: bool = True):
        self.base_data_type = DataType(base_data_type)
        self.dct_type = dct_type
        self.base_type_encoding = base_type_encoding
        self.is_highlow_byte_order = is_highlow_byte_order

    def _extract_internal(self,
                          coded_message: bytes,
                          byte_position: int,
                          bit_position: int,
                          bit_length: int,
                          base_data_type: DataType,
                          is_highlow_byte_order: bool,
                          bit_mask: Optional[int] = None):
        """Extract the internal value.

        Helper method for `DiagCodedType.convert_bytes_to_internal`.
        """
        # If the bit length is zero, return "empty" values of each type
        if bit_length == 0:
            return base_data_type.as_python_type()(), byte_position

        byte_length = (bit_length + bit_position + 7) // 8
        if byte_position + byte_length > len(coded_message):
            raise DecodeError(
                f"Expected a longer message."
            )
        next_byte_position = byte_position + byte_length
        extracted_bytes = coded_message[byte_position:next_byte_position]

        # TODO: Apply bit mask, etc.
        if bit_mask is not None:
            raise NotImplementedError(
                f"Don't know how to handle bit_mask={bit_mask}.")

        # Apply byteorder
        if not is_highlow_byte_order and base_data_type not in [DataType.A_UNICODE2STRING, DataType.A_BYTEFIELD, DataType.A_ASCIISTRING, DataType.A_UTF8STRING]:
            extracted_bytes = extracted_bytes[::-1]

        format_letter = ODX_TYPE_TO_FORMAT_LETTER[base_data_type]
        padding = 8 * byte_length - (bit_length + bit_position)
        internal_value = bitstruct.unpack_from(
            f"{format_letter}{bit_length}", extracted_bytes, offset=padding)[0]

        if base_data_type == DataType.A_UNICODE2STRING:
            # Convert bytes to string with utf-16 decoding
            if is_highlow_byte_order:
                internal_value = internal_value.decode("utf-16-be")
            else:
                internal_value = internal_value.decode("utf-16-le")

        return internal_value, next_byte_position

    def _to_bytes(self, internal_value, bit_position, bit_length, base_data_type, is_highlow_byte_order, bit_mask=None):
        """Convert the internal_value to bytes."""
        # Check that bytes and strings actually fit into the bit length
        if base_data_type in [DataType.A_BYTEFIELD] and 8 * len(internal_value) > bit_length:
            raise EncodeError(f"The bytefield {internal_value.hex()} is too large."
                              f" The maximum byte length is {bit_length//8}.")
        if base_data_type in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING] and 8 * len(internal_value) > bit_length:
            raise EncodeError(f"The string {repr(internal_value)} is too large."
                              f" The maximum number of characters is {bit_length//8}.")
        if base_data_type in [DataType.A_UNICODE2STRING] and 16 * len(internal_value) > bit_length:
            raise EncodeError(f"The string {repr(internal_value)} is too large."
                              f" The maximum number of characters is {bit_length//16}.")

        # If the bit length is zero, return empty bytes
        if bit_length == 0:
            if base_data_type in [DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64] and base_data_type != 0:
                raise EncodeError(
                    f"The number {repr(internal_value)} cannot be encoded into {bit_length} bits.")
            return bytes()

        char = ODX_TYPE_TO_FORMAT_LETTER[base_data_type]

        # The coded byte is divided into (0..0)(value)(0..0) with bit lengths (left_pad)(bit_length)(bit_position)
        offset = (8 - ((bit_length + bit_position) % 8)) % 8
        assert 0 <= offset and offset < 8 and (
            offset + bit_length + bit_position) % 8 == 0, f"Computational mistake, offset={offset}"
        left_pad = f'p{offset}' if offset > 0 else ''

        # Convert string to bytes with utf-16 encoding
        if base_data_type == DataType.A_UNICODE2STRING:
            if is_highlow_byte_order:
                internal_value = internal_value.encode("utf-16-be")
            else:
                internal_value = internal_value.encode("utf-16-le")

        code = bitstruct.pack(f'{left_pad}{char}{bit_length}', internal_value)

        if not is_highlow_byte_order and base_data_type not in [DataType.A_UNICODE2STRING, DataType.A_BYTEFIELD, DataType.A_ASCIISTRING, DataType.A_UTF8STRING]:
            code = code[::-1]

        # TODO: Apply bit mask.
        if bit_mask is not None:
            raise NotImplementedError(
                f"Don't know how to handle bit_mask={bit_mask}."
            )

        return code

    def _minimal_byte_length_of(self, internal_value: Union[bytes, str]) -> int:
        """Helper method to get the minimal byte length.
        (needed for LeadingLength- and MinMaxLengthType)
        """
        # A_BYTEFIELD, A_ASCIISTRING, A_UNICODE2STRING, A_UTF8STRING
        if self.base_data_type == DataType.A_BYTEFIELD:
            byte_length = len(internal_value)
        elif self.base_data_type in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING]:
            assert isinstance(internal_value, str)
            # TODO: Handle different encodings
            byte_length = len(bytes(internal_value, "utf-8"))
        elif self.base_data_type == DataType.A_UNICODE2STRING:
            assert isinstance(internal_value, str)
            byte_length = len(bytes(internal_value, "utf-16-le"))
            assert byte_length % 2 == 0, (f"The bit length of A_UNICODE2STRING must"
                                          f" be a multiple of 16 but is {8*byte_length}")
        return byte_length

    @abc.abstractmethod
    def convert_internal_to_bytes(self,
                                  internal_value: Any,
                                  encode_state: EncodeState,
                                  bit_position: int) \
                                  -> Union[bytes, bytearray]:
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
        pass

    @abc.abstractmethod
    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0) -> Any:
        """Decode the parameter value from the coded message.

        Parameters
        ----------
        decode_state : DecodeState
            The decoding state

        Returns
        -------
        str or int or bytes or bytearray or dict
            the decoded parameter value
        int
            the next byte position after the extracted parameter
        """
        pass


class LeadingLengthInfoType(DiagCodedType):
    def __init__(self,
                 base_data_type,
                 bit_length,
                 base_type_encoding=None,
                 is_highlow_byte_order=True):
        super().__init__(base_data_type,
                         dct_type="LEADING-LENGTH-INFO-TYPE",
                         base_type_encoding=base_type_encoding,
                         is_highlow_byte_order=is_highlow_byte_order)
        self.bit_length = bit_length
        assert self.bit_length > 0, "A Leading length info type with bit length == 0 does not make sense."
        assert self.base_data_type in [DataType.A_BYTEFIELD, DataType.A_ASCIISTRING, DataType.A_UNICODE2STRING, DataType.A_UTF8STRING], (
            f"A leading length info type cannot have the base data type {self.base_data_type}."
        )

    def convert_internal_to_bytes(self,
                                  internal_value: Any,
                                  encode_state: EncodeState,
                                  bit_position: int) \
                                  -> Union[bytes, bytearray]:

        byte_length = self._minimal_byte_length_of(internal_value)

        length_byte = self._to_bytes(byte_length,
                                     bit_position=bit_position,
                                     bit_length=self.bit_length,
                                     base_data_type=DataType.A_UINT32,
                                     is_highlow_byte_order=self.is_highlow_byte_order)

        value_byte = self._to_bytes(internal_value,
                                    bit_position=0,
                                    bit_length=8*byte_length,
                                    base_data_type=self.base_data_type,
                                    is_highlow_byte_order=self.is_highlow_byte_order)

        return length_byte + value_byte

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        coded_message = decode_state.coded_message

        # Extract length of the parameter value
        byte_length, byte_position = self._extract_internal(coded_message=coded_message,
                                                            byte_position=decode_state.next_byte_position,
                                                            bit_position=bit_position,
                                                            bit_length=self.bit_length,
                                                            base_data_type=DataType.A_UINT32,  # length is an integer
                                                            is_highlow_byte_order=self.is_highlow_byte_order)

        # Extract actual value
        # TODO: The returned value is None if the byte_length is 0. Maybe change it
        #       to some default value like an empty bytearray() or 0?
        value, next_byte_position = self._extract_internal(coded_message=coded_message,
                                                           byte_position=byte_position,
                                                           bit_position=0,
                                                           bit_length=8*byte_length,
                                                           base_data_type=self.base_data_type,
                                                           is_highlow_byte_order=self.is_highlow_byte_order)

        return value, next_byte_position

    def __repr__(self) -> str:
        repr_str = f"LeadingLengthInfoType(base_data_type='{self.base_data_type}', bit_length={self.bit_length}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()


class MinMaxLengthType(DiagCodedType):
    def __init__(self,
                 base_data_type,
                 min_length,
                 termination,
                 max_length=None,
                 base_type_encoding=None,
                 is_highlow_byte_order=True):
        super().__init__(base_data_type,
                         dct_type="MIN-MAX-LENGTH-TYPE",
                         base_type_encoding=base_type_encoding,
                         is_highlow_byte_order=is_highlow_byte_order)
        assert max_length is None or min_length <= max_length
        self.min_length = min_length
        self.max_length = max_length
        self.termination = termination

        assert self.base_data_type in [DataType.A_BYTEFIELD, DataType.A_ASCIISTRING, DataType.A_UNICODE2STRING, DataType.A_UTF8STRING], (
            f"A min-max length type cannot have the base data type {self.base_data_type}."
        )
        assert self.termination in ["ZERO", "HEX-FF", "END-OF-PDU"], (
            f"A min-max length type cannot have the termination {self.termination}"
        )

    def __termination_character(self):
        """Returns the termination character or None if it isn't defined."""
        # The termination character is actually not specified by ASAM
        # for A_BYTEFIELD but I assume it is only one byte.
        termination_char = None
        if self.termination == "ZERO":
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_char = bytes([0x0])
            else:
                termination_char = bytes([0x0, 0x0])
        elif self.termination == "HEX-FF":
            if self.base_data_type not in [DataType.A_UNICODE2STRING]:
                termination_char = bytes([0xff])
            else:
                termination_char = bytes([0xff, 0xff])
        return termination_char

    def convert_internal_to_bytes(self, internal_value, encode_state: EncodeState, bit_position: int) -> bytes:
        byte_length = self._minimal_byte_length_of(internal_value)

        # The coded value must have at least length min_length
        if byte_length < self.min_length:
            raise EncodeError(f"The internal value {internal_value} is only {byte_length} bytes"
                              f" long but the min length is {self.min_length}")
        # The coded value must not have a length greater than max_length
        if self.max_length and byte_length > self.max_length:
            raise EncodeError(f"The internal value {internal_value} requires {byte_length}"
                              f" bytes, but the max length is {self.max_length}")

        value_byte = self._to_bytes(internal_value,
                                    bit_position=0,
                                    bit_length=8*byte_length,
                                    base_data_type=self.base_data_type,
                                    is_highlow_byte_order=self.is_highlow_byte_order)

        if encode_state.is_end_of_pdu or byte_length == self.max_length:
            # All termination types may be ended by the PDU
            return value_byte
        else:
            termination_char = self.__termination_character()
            if self.termination == 'END-OF-PDU':
                termination_char = bytes()
            assert termination_char is not None, \
                (f"MinMaxLengthType with termination {self.termination}"
                 f"(min: {self.min_length}, max: {self.max_length}) failed encoding {internal_value}")
            return value_byte + termination_char

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        if decode_state.next_byte_position + self.min_length > len(decode_state.coded_message):
            raise DecodeError("The PDU ended before min length was reached.")

        coded_message = decode_state.coded_message
        byte_position = decode_state.next_byte_position
        termination_char = self.__termination_character()

        # If no termination char is found, this is the next byte after the parameter.
        max_termination_byte = len(coded_message)
        if self.max_length is not None:
            max_termination_byte = min(max_termination_byte, byte_position + self.max_length)

        if self.termination != "END-OF-PDU":
            # The parameter either ends after max length, at the end of the PDU
            # or if a termination character is found.
            char_length = len(termination_char)  # either 1 or 2

            termination_byte = byte_position + self.min_length
            found_char = False
            # Search the termination character
            while termination_byte < max_termination_byte and not found_char:
                found_char = coded_message[termination_byte: termination_byte +
                                           char_length] == termination_char
                if not found_char:
                    termination_byte += char_length

            byte_length = termination_byte - byte_position

            # Extract the value
            value, byte = self._extract_internal(decode_state.coded_message,
                                                 byte_position=byte_position,
                                                 bit_position=bit_position,
                                                 bit_length=8*byte_length,
                                                 base_data_type=self.base_data_type,
                                                 is_highlow_byte_order=self.is_highlow_byte_order)
            assert byte == termination_byte

            # next byte starts after the termination character
            next_byte_position = byte+char_length if found_char else byte
            return value, next_byte_position
        else:
            # If termination == "END-OF-PDU", the parameter ends after max_length
            # or at the end of the PDU.
            byte_length = max_termination_byte - byte_position

            value, byte = self._extract_internal(decode_state.coded_message,
                                                 byte_position=byte_position,
                                                 bit_position=bit_position,
                                                 bit_length=8*byte_length,
                                                 base_data_type=self.base_data_type,
                                                 is_highlow_byte_order=self.is_highlow_byte_order)
            return value, byte

    def __repr__(self) -> str:
        repr_str = f"MinMaxLengthType(base_data_type='{self.base_data_type}', min_length={self.min_length}"
        if self.max_length is not None:
            repr_str += f", base_type_encoding={self.max_length}"
        if self.termination is not None:
            repr_str += f", termination={self.termination}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()


class ParamLengthInfoType(DiagCodedType):
    def __init__(self,
                 base_data_type: Union[str, DataType],
                 length_key_id: OdxLinkId,
                 base_type_encoding=None,
                 is_highlow_byte_order=True):
        super().__init__(base_data_type,
                         dct_type="PARAM-LENGTH-INFO-TYPE",
                         base_type_encoding=base_type_encoding,
                         is_highlow_byte_order=is_highlow_byte_order)
        self.length_key_id = length_key_id

    def convert_internal_to_bytes(self, internal_value, encode_state: EncodeState, bit_position: int) -> bytes:
        bit_length = encode_state.length_keys.get(self.length_key_id, None)

        if bit_length is None:
            if self.base_data_type in [DataType.A_BYTEFIELD, DataType.A_ASCIISTRING, DataType.A_UTF8STRING]:
                bit_length = 8 * len(internal_value)
            if self.base_data_type in [DataType.A_UNICODE2STRING]:
                bit_length = 16 * len(internal_value)
        
            if self.base_data_type in [DataType.A_INT32, DataType.A_UINT32]:
                bit_length = int(internal_value).bit_length()
                if self.base_data_type == DataType.A_INT32:
                    bit_length += 1
                # Round up
                bit_length = math.ceil(bit_length / 8.0) * 8

        assert bit_length is not None
        encode_state.length_keys[self.length_key_id] = bit_length

        return self._to_bytes(internal_value,
                              bit_position=bit_position,
                              bit_length=bit_length,
                              base_data_type=self.base_data_type,
                              is_highlow_byte_order=self.is_highlow_byte_order)

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        # Find length key with matching ID.
        bit_length = 0
        for parameter, value in decode_state.parameter_value_pairs:
            # if isinstance(param_value.parameter, LengthKeyParameter) would be prettier,
            # but leads to cyclic import...
            if parameter.parameter_type == "LENGTH-KEY" \
                    and parameter.odx_id == self.length_key_id: # type: ignore
                # The bit length of the parameter to be extracted is given by the length key.
                assert isinstance(value, int)
                bit_length = value
                break

        assert bit_length is not None, f"Did not find any length key with ID {self.length_key_id}"

        # Extract the internal value and return.
        return self._extract_internal(decode_state.coded_message,
                                      decode_state.next_byte_position,
                                      bit_position,
                                      bit_length,
                                      self.base_data_type,
                                      self.is_highlow_byte_order)

    def __repr__(self) -> str:
        repr_str = f"ParamLengthInfoType(base_data_type='{self.base_data_type}', length_key_id={self.length_key_id}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()


class StandardLengthType(DiagCodedType):

    def __init__(self,
                 base_data_type: Union[str, DataType],
                 bit_length: int,
                 bit_mask=None,
                 condensed: bool = False,
                 base_type_encoding=None,
                 is_highlow_byte_order=True):
        super().__init__(base_data_type,
                         dct_type="STANDARD-LENGTH-TYPE",
                         base_type_encoding=base_type_encoding,
                         is_highlow_byte_order=is_highlow_byte_order)
        self.bit_length = bit_length
        self.bit_mask = bit_mask
        self.condensed = condensed

    def convert_internal_to_bytes(self, internal_value, encode_state: EncodeState, bit_position: int) -> bytes:
        return self._to_bytes(internal_value,
                              bit_position,
                              self.bit_length,
                              self.base_data_type,
                              is_highlow_byte_order=self.is_highlow_byte_order,
                              bit_mask=self.bit_mask)

    def convert_bytes_to_internal(self, decode_state: DecodeState, bit_position: int = 0):
        return self._extract_internal(decode_state.coded_message,
                                      decode_state.next_byte_position,
                                      bit_position,
                                      self.bit_length,
                                      self.base_data_type,
                                      self.is_highlow_byte_order,
                                      bit_mask=self.bit_mask)

    def __repr__(self) -> str:
        repr_str = f"StandardLengthType(base_data_type='{self.base_data_type}', bit_length={self.bit_length}"
        if self.bit_mask is not None:
            repr_str += f", bit_mask={self.bit_mask}"
        if self.condensed:
            repr_str += f", condensed={self.condensed}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()


def read_diag_coded_type_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    base_type_encoding = et_element.get("BASE-TYPE-ENCODING")

    base_data_type = et_element.get("BASE-DATA-TYPE")
    assert base_data_type in ["A_INT32", "A_UINT32", "A_FLOAT32", "A_FLOAT64",
                              "A_ASCIISTRING", "A_UTF8STRING", "A_UNICODE2STRING", "A_BYTEFIELD"]

    if et_element.get("IS-HIGHLOW-BYTE-ORDER") is not None:
        assert et_element.get("IS-HIGHLOW-BYTE-ORDER") in ["true", "false"]
        is_highlow_byte_order = et_element.get(
            "IS-HIGHLOW-BYTE-ORDER") == "true"
        logger.debug(
            f"HIGH-LOW-BYTE-ORDER set to {is_highlow_byte_order}")
    else:
        is_highlow_byte_order = True

    dct_type = et_element.get(f"{xsi}type")
    bit_length = None
    if dct_type == "LEADING-LENGTH-INFO-TYPE":
        bit_length = int(et_element.find("BIT-LENGTH").text)
        return LeadingLengthInfoType(base_data_type,
                                     bit_length=bit_length,
                                     base_type_encoding=base_type_encoding,
                                     is_highlow_byte_order=is_highlow_byte_order)
    elif dct_type == "MIN-MAX-LENGTH-TYPE":
        min_length = int(et_element.find("MIN-LENGTH").text)
        max_length = None
        if et_element.find("MAX-LENGTH"):
            max_length = int(et_element.find("MAX-LENGTH").text)
        termination = et_element.get("TERMINATION")

        return MinMaxLengthType(base_data_type,
                                min_length=min_length,
                                max_length=max_length,
                                termination=termination,
                                base_type_encoding=base_type_encoding,
                                is_highlow_byte_order=is_highlow_byte_order)
    elif dct_type == "PARAM-LENGTH-INFO-TYPE":
        # TODO: This is a bit hacky: we make an ID where the data
        # specifies a reference. The reason is that we need to store
        # the result in an associative array which is not possible
        # with references. Note that we currently ignore the DOCREF
        # attribute of the reference, so if there are any ID conflicts
        # between document fragments, the encoding process will go
        # wrong...
        length_key_elem = et_element.find("LENGTH-KEY-REF")
        length_key_id = OdxLinkId(length_key_elem.attrib["ID-REF"], doc_frags)

        return ParamLengthInfoType(base_data_type,
                                   length_key_id,
                                   base_type_encoding=base_type_encoding,
                                   is_highlow_byte_order=is_highlow_byte_order)
    elif dct_type == "STANDARD-LENGTH-TYPE":
        bit_length = int(et_element.find("BIT-LENGTH").text)
        bit_mask = None
        if et_element.find("BIT-MASK"):
            bit_mask = et_element.find("BIT-MASK").text
        condensed = et_element.get("CONDENSED") == "true"
        return StandardLengthType(base_data_type,
                                  bit_length,
                                  bit_mask=bit_mask,
                                  condensed=condensed,
                                  base_type_encoding=base_type_encoding,
                                  is_highlow_byte_order=is_highlow_byte_order)
    raise NotImplementedError(f"I do not know the diag-coded-type {dct_type}")
