# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from .odxtypes import DataType
from .odxlink import OdxDocFragment

class Radix(Enum):
    HEX = "HEX"
    DEC = "DEC"
    BIN = "BIN"
    OCT = "OCT"


@dataclass
class PhysicalType:
    """The physical type describes the base data type of a parameter.

    Similar to how a `DiagCodedType` describes the encoding of the internal value,
    the `PhysicalType` describes how to display the physical value.

    For an unsigned integers (A_UINT32) it may specify a display radix (HEX, DEC, BIN, OCT).
    For floating point numbers (A_FLOAT32, A_FLOAT64) it may specify a precision,
    that is, the number of digits to display after the decimal point.

    Examples
    --------

    A hexadecimal, integer number::

    PhysicalType(DataType.A_UINT32, display_radix=Radix.HEX)

    A floating point number that should be displayed with 2 digits after the decimal point::

    PhysicalType(DataType.A_FLOAT64, precision=2)
    """

    base_data_type: DataType

    display_radix: Optional[Radix] = None
    """The display radix defines how integers are displayed to the user.
    The display radix is only applicable if the base data type is A_UINT32. 
    """

    precision: Optional[int] = None
    """Number of digits after the decimal point to display to the user
    The precision is only applicable if the base data type is A_FLOAT32 or A_FLOAT64. 
    """

    def __post_init__(self):
        self.base_data_type = DataType(self.base_data_type)
        if self.display_radix is not None:
            self.display_radix = Radix(self.display_radix)


def read_physical_type_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    base_data_type = et_element.get("BASE-DATA-TYPE")
    assert base_data_type in ["A_INT32", "A_UINT32", "A_FLOAT32", "A_FLOAT64",
                              "A_ASCIISTRING", "A_UTF8STRING", "A_UNICODE2STRING", "A_BYTEFIELD"]
    display_radix = et_element.get("DISPLAY-RADIX")
    precision = et_element.findtext("PRECISION")
    if precision is not None:
        precision = int(precision)

    return PhysicalType(base_data_type,
                        display_radix=display_radix,
                        precision=precision)
