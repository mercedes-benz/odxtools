# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest
from xml.etree import ElementTree

from odxtools.compumethods import Limit, LinearCompuMethod, IntervalType, TabIntpCompuMethod
from odxtools.compumethods.readcompumethod import read_compu_method_from_odx
from odxtools.exceptions import DecodeError, EncodeError
from odxtools.odxtypes import DataType


class TestLinearCompuMethod(unittest.TestCase):
    def test_linear_compu_method_type_int_int(self):
        compu_method = LinearCompuMethod(1, 3, "A_INT32", "A_INT32")

        self.assertEqual(compu_method.convert_internal_to_physical(4), 13)
        self.assertEqual(compu_method.convert_internal_to_physical(0), 1)
        self.assertEqual(compu_method.convert_internal_to_physical(-2), -5)

        self.assertEqual(compu_method.convert_physical_to_internal(13), 4)
        self.assertEqual(compu_method.convert_physical_to_internal(1), 0)
        self.assertEqual(compu_method.convert_physical_to_internal(-5), -2)

    def test_linear_compu_method_type_int_float(self):
        compu_method = LinearCompuMethod(1, 3, "A_INT32", "A_FLOAT32")
        self.assertTrue(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value("123"))
        self.assertFalse(compu_method.is_valid_internal_value(1.2345))

        self.assertTrue(compu_method.is_valid_physical_value(1.2345))
        self.assertTrue(compu_method.is_valid_physical_value(123))
        self.assertFalse(compu_method.is_valid_physical_value("123"))

    def test_linear_compu_method_type_float_int(self):
        compu_method = LinearCompuMethod(1, 3, "A_FLOAT32", "A_INT32")
        self.assertTrue(compu_method.is_valid_internal_value(1.2345))
        self.assertTrue(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value("123"))

        self.assertTrue(compu_method.is_valid_physical_value(123))
        self.assertFalse(compu_method.is_valid_physical_value("123"))
        self.assertFalse(compu_method.is_valid_physical_value(1.2345))

    def test_linear_compu_method_type_string(self):
        compu_method = LinearCompuMethod(
            1, 3, "A_ASCIISTRING", "A_UNICODE2STRING")
        self.assertTrue(compu_method.is_valid_internal_value("123"))
        self.assertFalse(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value(1.2345))

    def test_linear_compu_method_limits(self):
        compu_method = LinearCompuMethod(1, 5, "A_INT32", "A_INT32",
                                         internal_lower_limit=Limit(2),
                                         internal_upper_limit=Limit(15))
        self.assertFalse(compu_method.is_valid_internal_value(-3))
        self.assertFalse(compu_method.is_valid_internal_value(1))
        self.assertFalse(compu_method.is_valid_internal_value(16))

        self.assertTrue(compu_method.is_valid_internal_value(2))
        self.assertTrue(compu_method.is_valid_internal_value(15))
        self.assertTrue(compu_method.is_valid_internal_value(7))

        self.assertFalse(compu_method.is_valid_physical_value(10))
        self.assertFalse(compu_method.is_valid_physical_value(77))

        self.assertTrue(compu_method.is_valid_physical_value(11))
        self.assertTrue(compu_method.is_valid_physical_value(21))
        self.assertTrue(compu_method.is_valid_physical_value(76))

        self.assertEqual(compu_method.convert_internal_to_physical(4), 21)
        self.assertEqual(compu_method.convert_physical_to_internal(21), 4)

    def test_linear_compu_method_physical_limits(self):
        # Define decoding function: f: (2, 15] -> [-74, -14], f(x) = -5*x + 1
        compu_method = LinearCompuMethod(1, -5, "A_INT32", "A_INT32",
                                         internal_lower_limit=Limit(2,
                                                                    interval_type=IntervalType.OPEN),
                                         internal_upper_limit=Limit(15))

        self.assertEqual(compu_method.physical_lower_limit,
                         Limit(-74, interval_type=IntervalType.CLOSED))
        self.assertEqual(compu_method.physical_upper_limit,
                         Limit(-14, interval_type=IntervalType.CLOSED))

        self.assertTrue(compu_method.is_valid_internal_value(3))
        self.assertTrue(compu_method.is_valid_internal_value(15))
        self.assertFalse(compu_method.is_valid_internal_value(2))
        self.assertFalse(compu_method.is_valid_internal_value(16))

        self.assertTrue(compu_method.is_valid_physical_value(-74))
        self.assertTrue(compu_method.is_valid_physical_value(-14))
        self.assertFalse(compu_method.is_valid_physical_value(-75))
        self.assertFalse(compu_method.is_valid_physical_value(-13))


class TestTabIntpCompuMethod(unittest.TestCase):
    def test_tabintp_convert_type_int_float(self):
        method = TabIntpCompuMethod("A_INT32",
                                    "A_FLOAT32",
                                    internal_points=[0, 10, 30],
                                    physical_points=[-1, 1, 2]
                                    )

        for internal, physical in [
            (0, -1),
            (2, -0.6),
            (3, -0.4),
            (5, 0),
            (10, 1),
            (20, 1.5),
            (25, 1.75),
            (30, 2)
        ]:
            self.assertTrue(method.is_valid_internal_value(internal))
            self.assertTrue(method.is_valid_physical_value(physical))
            self.assertEqual(method.convert_internal_to_physical(internal),
                             physical)
            self.assertEqual(method.convert_physical_to_internal(physical),
                             internal)

        self.assertRaises(DecodeError,
                          method.convert_internal_to_physical, -2)
        self.assertRaises(DecodeError,
                          method.convert_internal_to_physical, 31)
        self.assertRaises(EncodeError,
                          method.convert_physical_to_internal, -2)
        self.assertRaises(EncodeError,
                          method.convert_physical_to_internal, 2.1)

    def test_read_odx(self):
        expected = TabIntpCompuMethod("A_INT32",
                                      "A_FLOAT32",
                                      internal_points=[0, 10, 30],
                                      physical_points=[-1, 1, 2]
                                      )

        sample_odx = f"""
            <COMPU-METHOD> 
                <CATEGORY>TAB-INTP</CATEGORY>
                <COMPU-INTERNAL-TO-PHYS>
                    <COMPU-SCALES>
                        <COMPU-SCALE>
                            <LOWER-LIMIT INTERVAL-TYPE = "CLOSED">{expected.internal_points[0]}</LOWER-LIMIT>
                            <COMPU-CONST>
                                <V>{expected.physical_points[0]}</V>
                            </COMPU-CONST>
                        </COMPU-SCALE>
                        <COMPU-SCALE>
                            <LOWER-LIMIT INTERVAL-TYPE = "CLOSED">{expected.internal_points[1]}</LOWER-LIMIT>
                            <COMPU-CONST>
                                <V>{expected.physical_points[1]}</V>
                            </COMPU-CONST>
                        </COMPU-SCALE>
                        <COMPU-SCALE>
                            <LOWER-LIMIT INTERVAL-TYPE = "CLOSED">{expected.internal_points[2]}</LOWER-LIMIT>
                            <COMPU-CONST>
                                <V>{expected.physical_points[2]}</V>
                            </COMPU-CONST>
                        </COMPU-SCALE>
                    </COMPU-SCALES>
                </COMPU-INTERNAL-TO-PHYS>
            </COMPU-METHOD>
        """

        et_element = ElementTree.fromstring(sample_odx)
        actual = read_compu_method_from_odx(et_element,
                                            expected.internal_type, expected.physical_type)
        self.assertIsInstance(actual, TabIntpCompuMethod)
        self.assertEqual(expected.physical_type, actual.physical_type)
        self.assertEqual(expected.internal_type, actual.internal_type)
        self.assertEqual(expected.internal_points, actual.internal_points)
        self.assertEqual(expected.physical_points, actual.physical_points)


if __name__ == '__main__':
    unittest.main()
