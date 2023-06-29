# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import inspect
import os
import unittest
from xml.etree import ElementTree

import jinja2

import odxtools
from odxtools.compumethods import IntervalType, Limit, LinearCompuMethod, TabIntpCompuMethod
from odxtools.compumethods.createanycompumethod import create_any_compu_method_from_et
from odxtools.exceptions import DecodeError, EncodeError
from odxtools.odxlink import OdxDocFragment
from odxtools.odxtypes import DataType

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestLinearCompuMethod(unittest.TestCase):

    def setUp(self) -> None:
        """Prepares the jinja environment and the sample linear compumethod"""

        def _get_jinja_environment():
            __module_filename = inspect.getsourcefile(odxtools)
            assert isinstance(__module_filename, str)
            templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])

            jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))

            # allows to put XML attributes on a separate line while it is
            # collapsed with the previous line in the rendering
            jinja_env.filters["odxtools_collapse_xml_attribute"] = (lambda x: " " + x.strip()
                                                                    if x.strip() else "")

            jinja_env.globals["hasattr"] = hasattr
            return jinja_env

        self.jinja_env = _get_jinja_environment()

        self.linear_compumethod = LinearCompuMethod(
            offset=0,
            factor=1,
            denominator=3600,
            internal_type="A_INT32",
            physical_type="A_INT32",
            internal_lower_limit=None,
            internal_upper_limit=None,
        )

        self.linear_compumethod_odx = f"""
        <COMPU-METHOD>
            <CATEGORY>LINEAR</CATEGORY>
            <COMPU-INTERNAL-TO-PHYS>
                <COMPU-SCALES>
                    <COMPU-SCALE>
                        <COMPU-RATIONAL-COEFFS>
                            <COMPU-NUMERATOR>
                                <V>{self.linear_compumethod.offset}</V>
                                <V>{self.linear_compumethod.factor}</V>
                            </COMPU-NUMERATOR>
                            <COMPU-DENOMINATOR>
                                <V>{self.linear_compumethod.denominator}</V>
                            </COMPU-DENOMINATOR>
                        </COMPU-RATIONAL-COEFFS>
                    </COMPU-SCALE>
                </COMPU-SCALES>
            </COMPU-INTERNAL-TO-PHYS>
        </COMPU-METHOD>
        """

    def test_read_odx(self):
        """Test parsing of linear compumethod"""
        expected = self.linear_compumethod

        et_element = ElementTree.fromstring(self.linear_compumethod_odx)
        actual = create_any_compu_method_from_et(et_element, doc_frags, expected.internal_type,
                                                 expected.physical_type)
        self.assertIsInstance(actual, LinearCompuMethod)
        self.assertEqual(expected.physical_type, actual.physical_type)
        self.assertEqual(expected.internal_type, actual.internal_type)
        self.assertEqual(expected.offset, actual.offset)
        self.assertEqual(expected.factor, actual.factor)
        self.assertEqual(expected.denominator, actual.denominator)

    def test_write_odx(self):
        self.maxDiff = None
        dlc_tpl = self.jinja_env.get_template("macros/printDOP.xml.jinja2")
        module = dlc_tpl.make_module()

        out = module.printCompuMethod(self.linear_compumethod)

        expected_odx = self.linear_compumethod_odx

        # We ignore spaces
        def remove_spaces(string):
            return "".join(string.split())

        self.assertEqual(remove_spaces(out), remove_spaces(expected_odx))

    def test_linear_compu_method_type_denom_not_one(self):
        compu_method = LinearCompuMethod(
            offset=0,
            factor=1,
            denominator=3600,
            internal_type="A_INT32",
            physical_type="A_INT32",
            internal_lower_limit=None,
            internal_upper_limit=None,
        )
        self.assertEqual(compu_method.convert_physical_to_internal(2), 7200)

        self.assertEqual(compu_method.convert_internal_to_physical(7200), 2)

    def test_linear_compu_method_type_int_int(self):
        compu_method = LinearCompuMethod(
            offset=1,
            factor=3,
            denominator=1,
            internal_type="A_INT32",
            physical_type="A_INT32",
            internal_lower_limit=None,
            internal_upper_limit=None,
        )

        self.assertEqual(compu_method.convert_internal_to_physical(4), 13)
        self.assertEqual(compu_method.convert_internal_to_physical(0), 1)
        self.assertEqual(compu_method.convert_internal_to_physical(-2), -5)

        self.assertEqual(compu_method.convert_physical_to_internal(13), 4)
        self.assertEqual(compu_method.convert_physical_to_internal(1), 0)
        self.assertEqual(compu_method.convert_physical_to_internal(-5), -2)

    def test_linear_compu_method_type_int_float(self):
        compu_method = LinearCompuMethod(
            offset=1,
            factor=3,
            denominator=1,
            internal_type="A_INT32",
            physical_type="A_FLOAT32",
            internal_lower_limit=None,
            internal_upper_limit=None,
        )
        self.assertTrue(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value("123"))
        self.assertFalse(compu_method.is_valid_internal_value(1.2345))

        self.assertTrue(compu_method.is_valid_physical_value(1.2345))
        self.assertTrue(compu_method.is_valid_physical_value(123))
        self.assertFalse(compu_method.is_valid_physical_value("123"))

    def test_linear_compu_method_type_float_int(self):
        compu_method = LinearCompuMethod(
            offset=1,
            factor=3,
            denominator=1,
            internal_type="A_FLOAT32",
            physical_type="A_INT32",
            internal_lower_limit=None,
            internal_upper_limit=None,
        )
        self.assertTrue(compu_method.is_valid_internal_value(1.2345))
        self.assertTrue(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value("123"))

        self.assertTrue(compu_method.is_valid_physical_value(123))
        self.assertFalse(compu_method.is_valid_physical_value("123"))
        self.assertFalse(compu_method.is_valid_physical_value(1.2345))

    def test_linear_compu_method_type_string(self):
        compu_method = LinearCompuMethod(
            offset=1,
            factor=3,
            denominator=1,
            internal_type="A_ASCIISTRING",
            physical_type="A_UNICODE2STRING",
            internal_lower_limit=None,
            internal_upper_limit=None,
        )
        self.assertTrue(compu_method.is_valid_internal_value("123"))
        self.assertFalse(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value(1.2345))

    def test_linear_compu_method_limits(self):
        compu_method = LinearCompuMethod(
            offset=1,
            factor=5,
            denominator=1,
            internal_type="A_INT32",
            physical_type="A_INT32",
            internal_lower_limit=Limit(2),
            internal_upper_limit=Limit(15),
        )
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
        compu_method = LinearCompuMethod(
            offset=1,
            factor=-5,
            denominator=1,
            internal_type="A_INT32",
            physical_type="A_INT32",
            internal_lower_limit=Limit(2, interval_type=IntervalType.OPEN),
            internal_upper_limit=Limit(15),
        )

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

    def setUp(self) -> None:
        """Prepares the jinja environment and the sample tab-intp compumethod"""

        def _get_jinja_environment():
            __module_filename = inspect.getsourcefile(odxtools)
            assert isinstance(__module_filename, str)
            templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])

            jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))

            # allows to put XML attributes on a separate line while it is
            # collapsed with the previous line in the rendering
            jinja_env.filters["odxtools_collapse_xml_attribute"] = (lambda x: " " + x.strip()
                                                                    if x.strip() else "")

            jinja_env.globals["hasattr"] = hasattr
            return jinja_env

        self.jinja_env = _get_jinja_environment()

        self.compumethod = TabIntpCompuMethod(
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_FLOAT32,
            internal_points=[0, 10, 30],
            physical_points=[-1, 1, 2],
        )

        self.compumethod_odx = f"""
        <COMPU-METHOD>
            <CATEGORY>TAB-INTP</CATEGORY>
            <COMPU-INTERNAL-TO-PHYS>
                <COMPU-SCALES>
                    <COMPU-SCALE>
                        <LOWER-LIMIT INTERVAL-TYPE="CLOSED">{self.compumethod.internal_points[0]}</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>{self.compumethod.physical_points[0]}</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                    <COMPU-SCALE>
                        <LOWER-LIMIT INTERVAL-TYPE="CLOSED">{self.compumethod.internal_points[1]}</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>{self.compumethod.physical_points[1]}</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                    <COMPU-SCALE>
                        <LOWER-LIMIT INTERVAL-TYPE="CLOSED">{self.compumethod.internal_points[2]}</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>{self.compumethod.physical_points[2]}</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                </COMPU-SCALES>
            </COMPU-INTERNAL-TO-PHYS>
        </COMPU-METHOD>
        """

    def test_tabintp_convert_type_int_float(self):
        method = self.compumethod

        for internal, physical in [
            (0, -1),
            (2, -0.6),
            (3, -0.4),
            (5, 0),
            (10, 1),
            (20, 1.5),
            (25, 1.75),
            (30, 2),
        ]:
            self.assertTrue(method.is_valid_internal_value(internal))
            self.assertTrue(method.is_valid_physical_value(physical))
            self.assertEqual(method.convert_internal_to_physical(internal), physical)
            self.assertEqual(method.convert_physical_to_internal(physical), internal)

        self.assertRaises(DecodeError, method.convert_internal_to_physical, -2)
        self.assertRaises(DecodeError, method.convert_internal_to_physical, 31)
        self.assertRaises(EncodeError, method.convert_physical_to_internal, -2)
        self.assertRaises(EncodeError, method.convert_physical_to_internal, 2.1)

    def test_read_odx(self):
        expected = self.compumethod

        et_element = ElementTree.fromstring(self.compumethod_odx)
        actual = create_any_compu_method_from_et(et_element, doc_frags, expected.internal_type,
                                                 expected.physical_type)
        self.assertIsInstance(actual, TabIntpCompuMethod)
        self.assertEqual(expected.physical_type, actual.physical_type)
        self.assertEqual(expected.internal_type, actual.internal_type)
        self.assertEqual(expected.internal_points, actual.internal_points)
        self.assertEqual(expected.physical_points, actual.physical_points)

    def test_write_odx(self):
        dlc_tpl = self.jinja_env.get_template("macros/printDOP.xml.jinja2")
        module = dlc_tpl.make_module()

        out = module.printCompuMethod(self.compumethod)

        expected_odx = self.compumethod_odx

        # We ignore spaces
        def remove_spaces(string):
            return "".join(string.split())

        self.assertEqual(remove_spaces(out), remove_spaces(expected_odx))


if __name__ == "__main__":
    unittest.main()
