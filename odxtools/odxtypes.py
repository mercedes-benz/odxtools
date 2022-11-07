# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from enum import Enum
from typing import Any, Callable, Dict, Literal, Type, Union

def bytefield_to_bytearray(bytefield: str) -> bytearray:
    bytes_string = [bytefield[i:i+2] for i in range(0, len(bytefield), 2)]
    return bytearray(map(lambda x: int(x, 16), bytes_string))

PythonType = Union[str, int, float, bytearray]
LiteralPythonType = Type[Union[str, int, float, bytearray]]

def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        v = float(value)
        assert v.is_integer()
        return int(v)

_ODX_TYPE_PARSER: Dict[str, Callable[[str], PythonType]] = {
    "A_INT32": parse_int,
    "A_UINT32": parse_int,
    "A_FLOAT32": float,
    "A_FLOAT64": float,
    "A_UNICODE2STRING": str,
    "A_BYTEFIELD": bytefield_to_bytearray,
    # only in DATA-TYPE not in PHYSICAL-DATA-TYPE
    "A_ASCIISTRING": str,
    "A_UTF8STRING": str
}

_ODX_TYPE_TO_PYTHON_TYPE: Dict[str, LiteralPythonType] = {
    "A_INT32": int,
    "A_UINT32": int,
    "A_FLOAT32": float,
    "A_FLOAT64": float,
    "A_UNICODE2STRING": str,
    "A_BYTEFIELD": bytearray,
    # only in DATA-TYPE not in PHYSICAL-DATA-TYPE
    "A_ASCIISTRING": str,
    "A_UTF8STRING": str
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
    # only in DATA-TYPE not in PHYSICAL-DATA-TYPE
    A_ASCIISTRING = "A_ASCIISTRING"
    A_UTF8STRING = "A_UTF8STRING"

    def as_python_type(self) -> type:
        return _ODX_TYPE_TO_PYTHON_TYPE[self.value]

    def from_string(self, value: str) -> Union[int, float, str, bytearray]:
        return _ODX_TYPE_PARSER[self.value](value)

    def make_from(self, value: Any) -> Union[int, float, str, bytearray]:
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
