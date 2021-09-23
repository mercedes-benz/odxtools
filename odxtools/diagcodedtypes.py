# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import abc
from typing import Union
from odxtools.exceptions import DecodeError
from .globals import xsi, logger

import bitstruct

ODX_TYPE_TO_FORMAT_LETTER = {
    "A_INT32": 's',
    "A_UINT32": 'u',
    "A_FLOAT32": 'f',
    "A_FLOAT64": 'f',
    "A_BYTEFIELD": 'r',
    "A_UNICODE2STRING": 't',  # TODO: How to handle different string encodings?
    "A_ASCIISTRING": 't',
    "A_UTF8STRING": 't'
}


class DiagCodedType(abc.ABC):
    def __init__(self,
                 base_data_type: str,
                 dct_type: str,
                 base_type_encoding=None,
                 is_highlow_byte_order: bool = True):
        self.base_data_type = base_data_type
        self.dct_type = dct_type
        self.base_type_encoding = base_type_encoding
        self.is_highlow_byte_order = is_highlow_byte_order

    @abc.abstractclassmethod
    def convert_bytes_to_internal(self, coded_message: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        """Decode the parameter value from the coded message.

        Parameters
        ----------
        coded_message : bytes or bytearray
            the coded message
        byte_position : int or None
            Byte position of the parameter

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
        assert base_data_type in [
            "A_BYTEFIELD", "A_ASCIISTRING", "A_UNICODE2STRING", "A_UTF8STRING"]

    def convert_bytes_to_internal(self, coded_message: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        value = bytearray()
        num_bytes = 0
        byte_length = 0

        if self.bit_length > 0:
            byteorder = '>' if self.is_highlow_byte_order else '<'
            num_bytes = (self.bit_length + bit_position + 7) // 8
            bit_offset = 8 * (byte_position + num_bytes) - \
                bit_position - self.bit_length
            bit_offset_format = f"p{bit_offset}" if bit_offset > 0 else ""
            byte_length = bitstruct.unpack(
                f'{bit_offset_format}u{self.bit_length}{byteorder}', coded_message)[0]

            if byte_length > 0:
                bit_offset = 8 * (byte_position + num_bytes)
                bit_offset_format = f"p{bit_offset}" if bit_offset > 0 else ""
                format_letter = ODX_TYPE_TO_FORMAT_LETTER[self.base_data_type]
                value = bitstruct.unpack(
                    f'{bit_offset_format}{format_letter}{8 * byte_length}{byteorder}', coded_message)[0]

        return value, byte_position + num_bytes + byte_length

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
                 max_length=None,
                 termination=None,
                 base_type_encoding=None,
                 is_highlow_byte_order=True):
        super().__init__(base_data_type,
                         dct_type="MIN-MAX-LENGTH-TYPE",
                         base_type_encoding=base_type_encoding,
                         is_highlow_byte_order=is_highlow_byte_order)
        self.min_length = min_length
        self.max_length = max_length
        self.termination = termination

    def convert_bytes_to_internal(self, coded_message: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        raise NotImplementedError(
            'MinMaxLenthType decoding is not implemented.')

    def __repr__(self) -> str:
        repr_str = f"ParamLengthInfoType(base_data_type='{self.base_data_type}', min_length={self.min_length}"
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
                 base_data_type: str,
                 length_key_ref: str,
                 base_type_encoding=None,
                 is_highlow_byte_order=True):
        super().__init__(base_data_type,
                         dct_type="PARAM-LENGTH-INFO-TYPE",
                         base_type_encoding=base_type_encoding,
                         is_highlow_byte_order=is_highlow_byte_order)
        self.length_key_ref = length_key_ref

    def convert_bytes_to_internal(self, coded_message: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        raise NotImplementedError(
            'ParamLengthInfoType decoding is not implemented.')

    def __repr__(self) -> str:
        repr_str = f"ParamLengthInfoType(base_data_type='{self.base_data_type}', length_key_ref={self.length_key_ref}"
        if self.base_type_encoding is not None:
            repr_str += f", base_type_encoding={self.base_type_encoding}"
        if not self.is_highlow_byte_order:
            repr_str += f", is_highlow_byte_order={self.is_highlow_byte_order}"
        return repr_str + ")"

    def __str__(self) -> str:
        return self.__repr__()


class StandardLengthType(DiagCodedType):

    def __init__(self,
                 base_data_type: str,
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

    def convert_internal_to_bytes(self, internal_value, bit_position: int) -> Union[bytes, bytearray]:
        num_bytes = (self.bit_length + bit_position + 7) // 8
        # TODO: Apply bit mask, etc.
        if self.bit_mask is not None:
            raise NotImplementedError(
                f"Don't know how to handle bit_mask={self.bit_mask}.")
        byteorder = "big" if self.is_highlow_byte_order else "little"

        if isinstance(internal_value, (bytes, bytearray)):
            # Make sure the length is num_bytes and reverse order if necessary
            return int.from_bytes(internal_value, "big").to_bytes(num_bytes, byteorder)
        if isinstance(internal_value, int):
            internal_value = internal_value << bit_position
            return internal_value.to_bytes(num_bytes, byteorder)
        else:
            logger.warn(
                f"Can only convert integers to bytes, but not '{internal_value}' of type {type(internal_value)}.")
            try:
                return bytearray(internal_value)
            except:
                raise NotImplementedError(
                    f"Can only convert integers to bytes. Did not convert {type(internal_value)} to bytes")

    def convert_bytes_to_internal(self, coded_message: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        """Extract the bytes at the parameters's byte position and convert them to the internal value.

        Parameters
        ----------
        coded_message : bytes or bytearray
            the coded message
        byte_length : int
        byte_position : int or None
            Byte position of the parameter

        Returns
        -------
        bytes or bytearray
            the extracted bytes
        int
            the next byte position after the extracted parameter
        """
        byte_length = (self.bit_length + bit_position + 7) // 8
        if byte_position + byte_length > len(coded_message):
            raise DecodeError(
                f"Expected a longer message."
            )
        next_byte_position = byte_position+byte_length
        extracted_bytes = coded_message[byte_position:next_byte_position]

        # TODO: Apply bit mask, highlow byte order, etc.
        if self.bit_mask is not None:
            raise NotImplementedError(
                f"Don't know how to handle bit_mask={self.bit_mask}.")
        # Apply byteorder
        if not self.is_highlow_byte_order:
            extracted_bytes = extracted_bytes[::-1]
        format_letter = ODX_TYPE_TO_FORMAT_LETTER[self.base_data_type]
        padding = 8 * byte_length - (self.bit_length + bit_position)
        internal_value = bitstruct.unpack_from(
            f"{format_letter}{self.bit_length}", extracted_bytes, offset=padding)[0]
        return internal_value, next_byte_position

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


def read_diag_coded_type_from_odx(et_element):
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
        try:
            max_length = int(et_element.find("MAX-LENGTH").text)
        except:
            max_length = None
        termination = et_element.get("TERMINATION")

        return MinMaxLengthType(base_data_type,
                                min_length=min_length,
                                max_length=max_length,
                                termination=termination,
                                base_type_encoding=base_type_encoding,
                                is_highlow_byte_order=is_highlow_byte_order)
    elif dct_type == "PARAM-LENGTH-INFO-TYPE":
        length_key_ref = et_element.find(
            "LENGTH-KEY-REF").get("ID-REF")

        return ParamLengthInfoType(base_data_type,
                                   length_key_ref,
                                   base_type_encoding=base_type_encoding,
                                   is_highlow_byte_order=is_highlow_byte_order)
    elif dct_type == "STANDARD-LENGTH-TYPE":
        bit_length = int(et_element.find("BIT-LENGTH").text)
        try:
            bit_mask = et_element.find("BIT-MASK").text
        except:
            bit_mask = None
        condensed = et_element.get("CONDENSED") == "true"
        return StandardLengthType(base_data_type,
                                  bit_length,
                                  bit_mask=bit_mask,
                                  condensed=condensed,
                                  base_type_encoding=base_type_encoding,
                                  is_highlow_byte_order=is_highlow_byte_order)
    raise NotImplementedError(f"I do not know the diag-coded-type {dct_type}")
