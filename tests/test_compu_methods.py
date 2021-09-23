# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import unittest

from odxtools.compumethods import LinearCompuMethod


class TestLinearCompuMethod(unittest.TestCase):
    def test_linear_compu_method(self):
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
        compu_method = LinearCompuMethod(1, 3, "A_ASCIISTRING", "A_UNICODE2STRING")
        self.assertTrue(compu_method.is_valid_internal_value("123"))
        self.assertFalse(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value(1.2345))

    def test_linear_compu_method_limits(self):
        compu_method = LinearCompuMethod(1, 5, "A_INT32", "A_INT32", internal_lower_limit=2, internal_upper_limit=15)
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


if __name__ == '__main__':
    unittest.main()
