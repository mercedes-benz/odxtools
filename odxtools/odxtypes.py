# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

def bytefield_to_bytearray(bytefield : str) -> bytearray:
    bytes_string = [ bytefield[i:i+2] for i in range(0, len(bytefield), 2)]
    return bytearray(map(lambda x: int(x, 16), bytes_string))

ODX_TYPE_PARSER = {
    "A_INT32": int,
    "A_UINT32": int,
    "A_FLOAT32": float,
    "A_FLOAT64": float,
    "A_UNICODE2STRING": str,
    "A_BYTEFIELD": bytefield_to_bytearray,
    # only in DATA-TYPE not in PHYSICAL-DATA-TYPE
    "A_ASCIISTRING": str,
    "A_UTF8STRING": str
}

ODX_TYPE_TO_PYTHON_TYPE = {
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

def _odx_isinstance(value, odx_type):
    expected_type = ODX_TYPE_TO_PYTHON_TYPE[odx_type]
    if isinstance(value, expected_type):
        return True
    elif expected_type == float and isinstance(value, (int, float)):
        return True
    elif odx_type == "A_BYTEFIELD" and isinstance(value, (bytearray, bytes)):
        return True
    else:
        return False
