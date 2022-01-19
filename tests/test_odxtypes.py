# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest
from odxtools.odxtypes import DataType


class TestDataType(unittest.TestCase):

    def test_cast_string(self):
        self.assertTrue(DataType.A_UINT32 == DataType("A_UINT32"))

    def test_cast(self):
        self.assertTrue(DataType.A_UINT32.cast("12") == 12)
        self.assertTrue(DataType.A_FLOAT64.cast("3.14") == 3.14)
        self.assertTrue(DataType.A_INT32.cast(3.14) == 3)

        self.assertRaises(TypeError, DataType.A_BYTEFIELD.cast, "12")

        self.assertTrue(DataType.A_UINT32.cast_string("12") == 12)
        self.assertTrue(DataType.A_BYTEFIELD.cast_string("12")
                        == bytes([0x12]))

    def test_python_types(self):
        self.assertTrue(DataType.A_UINT32.as_python_type() == int)
        self.assertTrue(DataType.A_INT32.as_python_type() == int)
        self.assertTrue(DataType.A_FLOAT32.as_python_type() == float)
        self.assertTrue(DataType.A_FLOAT64.as_python_type() == float)
        self.assertTrue(DataType.A_BYTEFIELD.as_python_type() == bytearray)
        self.assertTrue(DataType.A_UNICODE2STRING.as_python_type() == str)
        self.assertTrue(DataType.A_UTF8STRING.as_python_type() == str)
        self.assertTrue(DataType.A_ASCIISTRING.as_python_type() == str)

    def test_isinstance(self):
        self.assertTrue(DataType.A_ASCIISTRING.isinstance("123"))
        self.assertTrue(DataType.A_BYTEFIELD.isinstance(bytes([0x12, 0x34])))
        self.assertTrue(DataType.A_UINT32.isinstance(123))
        self.assertTrue(DataType.A_FLOAT32.isinstance(123.456))
        # We allow integers as float values
        self.assertTrue(DataType.A_FLOAT32.isinstance(123))

        self.assertFalse(DataType.A_UINT32.isinstance(bytes([0x12])))
        self.assertFalse(DataType.A_BYTEFIELD.isinstance([0x12]))
        self.assertFalse(DataType.A_BYTEFIELD.isinstance(0x12))


if __name__ == '__main__':
    unittest.main()
