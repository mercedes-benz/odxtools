# SPDX-License-Identifier: MIT
import unittest

from odxtools.odxtypes import DataType


class TestDataType(unittest.TestCase):

    def test_from_string(self) -> None:
        self.assertTrue(DataType.A_UINT32 == DataType(DataType.A_UINT32))

    def test_make_from(self) -> None:
        self.assertTrue(DataType.A_UINT32.make_from("12") == 12)
        self.assertTrue(DataType.A_FLOAT64.make_from("3.14") == 3.14)
        self.assertTrue(DataType.A_INT32.make_from(3.14) == 3)

        self.assertTrue(DataType.A_BYTEFIELD.make_from("12") == b"\x12")

        self.assertTrue(DataType.A_UINT32.from_string("12") == 12)
        self.assertTrue(DataType.A_BYTEFIELD.from_string("12") == b"\x12")

    def test_python_types(self) -> None:
        self.assertTrue(DataType.A_UINT32.python_type is int)
        self.assertTrue(DataType.A_INT32.python_type is int)
        self.assertTrue(DataType.A_FLOAT32.python_type is float)
        self.assertTrue(DataType.A_FLOAT64.python_type is float)
        self.assertTrue(DataType.A_BYTEFIELD.python_type is bytearray)
        self.assertTrue(DataType.A_UNICODE2STRING.python_type is str)
        self.assertTrue(DataType.A_UTF8STRING.python_type is str)
        self.assertTrue(DataType.A_ASCIISTRING.python_type is str)

    def test_isinstance(self) -> None:
        self.assertTrue(DataType.A_ASCIISTRING.isinstance("123"))
        self.assertTrue(DataType.A_BYTEFIELD.isinstance(bytes([0x12, 0x34])))
        self.assertTrue(DataType.A_UINT32.isinstance(123))
        self.assertTrue(DataType.A_FLOAT32.isinstance(123.456))
        # We allow integers as float values
        self.assertTrue(DataType.A_FLOAT32.isinstance(123))

        self.assertFalse(DataType.A_UINT32.isinstance(bytes([0x12])))
        self.assertFalse(DataType.A_BYTEFIELD.isinstance([0x12]))
        self.assertFalse(DataType.A_BYTEFIELD.isinstance(0x12))


if __name__ == "__main__":
    unittest.main()
