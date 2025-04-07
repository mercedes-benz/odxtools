# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxraise
from .odxdoccontext import OdxDocContext
from .odxtypes import DataType
from .radix import Radix


@dataclass(kw_only=True)
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

    precision: int | None = None
    """Number of digits after the decimal point to display to the user
    The precision is only applicable if the base data type is A_FLOAT32 or A_FLOAT64.
    """

    base_data_type: DataType

    display_radix: Radix | None = None
    """The display radix defines how integers are displayed to the user.
    The display radix is only applicable if the base data type is A_UINT32.
    """

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "PhysicalType":
        precision_str = et_element.findtext("PRECISION")
        precision = int(precision_str) if precision_str is not None else None

        base_data_type_str = et_element.get("BASE-DATA-TYPE")
        if base_data_type_str not in DataType.__members__:
            odxraise(f"Encountered unknown base data type '{base_data_type_str}'")
        base_data_type = DataType(base_data_type_str)

        display_radix_str = et_element.get("DISPLAY-RADIX")
        if display_radix_str is not None:
            if display_radix_str not in Radix.__members__:
                odxraise(f"Encountered unknown display radix '{display_radix_str}'")
            display_radix = Radix.__members__[display_radix_str]
        else:
            display_radix = None

        return PhysicalType(
            precision=precision, base_data_type=base_data_type, display_radix=display_radix)
