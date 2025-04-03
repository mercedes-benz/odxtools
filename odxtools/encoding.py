# SPDX-License-Identifier: MIT
from enum import Enum

from .exceptions import odxraise
from .odxtypes import DataType


class Encoding(Enum):
    BCD_P = "BCD-P"
    BCD_UP = "BCD-UP"

    ONEC = "1C"
    TWOC = "2C"
    SM = "SM"

    UTF8 = "UTF-8"
    UCS2 = "UCS-2"
    ISO_8859_1 = "ISO-8859-1"
    ISO_8859_2 = "ISO-8859-2"
    WINDOWS_1252 = "WINDOWS-1252"

    NONE = "NONE"


def get_string_encoding(base_data_type: DataType, base_type_encoding: Encoding | None,
                        is_highlow_byte_order: bool) -> str | None:
    """If the encoding is for a string, return the value for
    `str.encode()`/`str.decode()` to convert the string object
    to/from a byte array
    """

    # note that the spec disallows certain combinations of
    # base_data_type and encoding (e.g., A_ASCIISTRING encoded
    # using UTF-8). Since in python3 strings are always
    # capable of the full unicode character set, odxtools
    # ignores these restrictions...
    if base_type_encoding == Encoding.UTF8 or (base_data_type == DataType.A_UTF8STRING and
                                               base_type_encoding is None):
        return "utf-8"
    elif base_type_encoding == Encoding.UCS2 or (base_data_type == DataType.A_UNICODE2STRING and
                                                 base_type_encoding is None):
        return "utf-16-be" if is_highlow_byte_order else "utf-16-le"
    elif base_type_encoding == Encoding.ISO_8859_1 or (base_data_type == DataType.A_ASCIISTRING and
                                                       base_type_encoding is None):
        return "iso-8859-1"
    elif base_type_encoding == Encoding.ISO_8859_2:
        return "iso-8859-2"
    elif base_type_encoding == Encoding.WINDOWS_1252:
        return "cp1252"
    else:
        odxraise(f"Specified illegal encoding {base_type_encoding} for {base_data_type.value} "
                 f"string object")
        return "iso-8859-1"

    return None
