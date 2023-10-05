# SPDX-License-Identifier: MIT
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, Union, overload
from xml.etree import ElementTree

from .exceptions import odxassert, odxraise, odxrequire

if TYPE_CHECKING:
    from odxtools.diagnostictroublecode import DiagnosticTroubleCode
    from odxtools.parameters.parameter import Parameter


def bytefield_to_bytearray(bytefield: str) -> bytearray:
    bytes_string = [bytefield[i:i + 2] for i in range(0, len(bytefield), 2)]
    return bytearray([int(x, 16) for x in bytes_string])


AtomicOdxType = Union[str, int, float, bytes]

# dictionary mapping short names to a Parameter that needs to be
# specified. Complex parameters (structures) may contain
# sub-parameters, so this is a recursive type...
ParameterDict = Dict[str, Union["Parameter", "ParameterDict"]]

# Dictionary mapping short names of parameters to the value it
# exhibits. Complex parameters (structures) may contain
# sub-parameters, so this is a recursive type, and fields encompass
# multiple items, so this can be a list of objects.
TableStructParameterValue = Tuple[str, "ParameterValue"]
ParameterValue = Union[AtomicOdxType, "ParameterValueDict", TableStructParameterValue,
                       List["ParameterValue"], "DiagnosticTroubleCode"]
ParameterValueDict = Dict[str, ParameterValue]


@overload
def odxstr_to_bool(str_val: None) -> None:
    ...


@overload
def odxstr_to_bool(str_val: str) -> bool:
    ...


def odxstr_to_bool(str_val: Optional[str]) -> Optional[bool]:
    if str_val is None:
        return None

    str_val = str_val.strip()
    odxassert(str_val in [
        "0",
        "1",
        "false",
        "true",
    ], f"String '{str_val}' cannot be converted to a boolean")

    return str_val in ["1", "true"]


def bool_to_odxstr(bool_val: bool) -> str:
    return "true" if bool_val else "false"


def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        try:
            v = float(value)
        except Exception as e:
            odxraise(f"Error parsing numerical value '{value}': {e}")

        if not v.is_integer():
            odxraise(f"Expected an integer value, got {v}")
        return int(v)


#: conversion functions for strings from the XML to the types stored
#: by the internalized database
_PARSE_ODX_TYPE: Dict[str, Callable[[str], AtomicOdxType]] = {
    "A_INT32": parse_int,
    "A_UINT32": parse_int,
    "A_FLOAT32": float,
    "A_FLOAT64": float,
    "A_UNICODE2STRING": str,
    "A_BYTEFIELD": bytefield_to_bytearray,
    "A_ASCIISTRING": str,
    "A_UTF8STRING": str,
}

#: mapping from type name strings specified by the XML to the types
#: used by the internalized database
_ODX_TYPE_TO_PYTHON_TYPE: Dict[str, Type[AtomicOdxType]] = {
    "A_INT32": int,
    "A_UINT32": int,
    "A_FLOAT32": float,
    "A_FLOAT64": float,
    "A_UNICODE2STRING": str,
    "A_BYTEFIELD": bytearray,
    "A_ASCIISTRING": str,
    "A_UTF8STRING": str,
}


class DataType(Enum):
    """Types for the physical and internal value.

    These types can be used either as BASE-DATA-TYPE (for the "internal value")
    or the PHYSICAL-DATA-TYPE (for the "physical value").

    Relevant pages in the ASAM MCD-2D specification:
    * p. 38 (Table 1): ASAM types correspondence with XML Schema types
    * p. 96: Restrictions to the bit length given the BASE-DATA-TYPE.
    """

    A_INT32 = "A_INT32"
    A_UINT32 = "A_UINT32"
    A_FLOAT32 = "A_FLOAT32"
    A_FLOAT64 = "A_FLOAT64"
    A_UNICODE2STRING = "A_UNICODE2STRING"
    A_BYTEFIELD = "A_BYTEFIELD"

    # these two enums are only used by internal data type objects (DATA-TYPE)
    # not by the ones for physical values (PHYSICAL-DATA-TYPE)
    A_ASCIISTRING = "A_ASCIISTRING"
    A_UTF8STRING = "A_UTF8STRING"

    def as_python_type(self) -> type:
        return _ODX_TYPE_TO_PYTHON_TYPE[self.value]

    def from_string(self, value: str) -> AtomicOdxType:
        return _PARSE_ODX_TYPE[self.value](value)

    @overload
    def create_from_et(self, et_element: None) -> None:
        ...

    @overload
    def create_from_et(self, et_element: ElementTree.Element) -> AtomicOdxType:
        ...

    def create_from_et(self, et_element: Optional[ElementTree.Element]) -> Optional[AtomicOdxType]:
        """
            Parse a V/VT value union and return an AtomicOdxType from them that match current datatype
            this includes, but not limited to COMPU-CONST, COMPU-DEFAULT-VALUE, COMPU-INVERSE-VALUE
        """
        if et_element is None:
            return None
        if (vt_elem := et_element.find("VT")) is not None:
            return self.from_string(odxrequire(vt_elem.text))
        elif (v_elem := et_element.find("V")) is not None:
            return self.from_string(odxrequire(v_elem.text))
        odxraise('Either V or VT needs to be specified')

    def make_from(self, value: Any) -> AtomicOdxType:
        if isinstance(value, str):
            # parse the string
            return self.from_string(value)
        else:
            # regular type cast of python objects
            return self.as_python_type()(value)

    def isinstance(self, value: Any) -> bool:
        expected_type = self.as_python_type()
        if isinstance(value, expected_type):
            return True
        elif expected_type == float and isinstance(value, (int, float)):
            return True
        elif self == DataType.A_BYTEFIELD and isinstance(value, (bytearray, bytes)):
            return True
        else:
            return False
