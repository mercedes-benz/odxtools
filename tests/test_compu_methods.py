# SPDX-License-Identifier: MIT
import inspect
import os
import unittest
from xml.etree import ElementTree

import jinja2

import odxtools
from odxtools.compumethods.compucodecompumethod import CompuCodeCompuMethod
from odxtools.compumethods.compuconst import CompuConst
from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuCategory
from odxtools.compumethods.compuphystointernal import CompuPhysToInternal
from odxtools.compumethods.compurationalcoeffs import CompuRationalCoeffs
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.createanycompumethod import create_any_compu_method_from_et
from odxtools.compumethods.limit import IntervalType, Limit
from odxtools.compumethods.linearcompumethod import LinearCompuMethod
from odxtools.compumethods.ratfunccompumethod import RatFuncCompuMethod
from odxtools.compumethods.scaleratfunccompumethod import ScaleRatFuncCompuMethod
from odxtools.compumethods.tabintpcompumethod import TabIntpCompuMethod
from odxtools.exceptions import DecodeError, EncodeError, OdxError
from odxtools.odxlink import OdxDocFragment
from odxtools.odxtypes import DataType
from odxtools.progcode import ProgCode
from odxtools.writepdxfile import (get_parent_container_name, jinja2_odxraise_helper,
                                   make_bool_xml_attrib, make_xml_attrib)

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestLinearCompuMethod(unittest.TestCase):

    def setUp(self) -> None:
        """Prepares the jinja environment and the sample linear compumethod"""

        def _get_jinja_environment() -> jinja2.environment.Environment:
            __module_filename = inspect.getsourcefile(odxtools)
            assert isinstance(__module_filename, str)
            templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])

            jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))

            jinja_env.globals["getattr"] = getattr
            jinja_env.globals["hasattr"] = hasattr
            jinja_env.globals["odxraise"] = jinja2_odxraise_helper
            jinja_env.globals["make_xml_attrib"] = make_xml_attrib
            jinja_env.globals["make_bool_xml_attrib"] = make_bool_xml_attrib
            jinja_env.globals["get_parent_container_name"] = get_parent_container_name

            return jinja_env

        self.jinja_env = _get_jinja_environment()

        self.linear_compumethod = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=None,
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[0, 1],
                            denominators=[3600],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32,
        )

        self.linear_compumethod_xml = f"""
        <COMPU-METHOD>
            <CATEGORY>LINEAR</CATEGORY>
            <COMPU-INTERNAL-TO-PHYS>
                <COMPU-SCALES>
                    <COMPU-SCALE>
                        <COMPU-RATIONAL-COEFFS>
                            <COMPU-NUMERATOR>
                                <V>{self.linear_compumethod.segment.offset}</V>
                                <V>{self.linear_compumethod.segment.factor}</V>
                            </COMPU-NUMERATOR>
                            <COMPU-DENOMINATOR>
                                <V>{self.linear_compumethod.segment.denominator}</V>
                            </COMPU-DENOMINATOR>
                        </COMPU-RATIONAL-COEFFS>
                    </COMPU-SCALE>
                </COMPU-SCALES>
            </COMPU-INTERNAL-TO-PHYS>
        </COMPU-METHOD>
        """

    def test_read_odx(self) -> None:
        """Test parsing of linear compumethod"""
        expected = self.linear_compumethod

        et_element = ElementTree.fromstring(self.linear_compumethod_xml)
        actual = create_any_compu_method_from_et(
            et_element,
            doc_frags,
            internal_type=expected.internal_type,
            physical_type=expected.physical_type)
        self.assertIsInstance(actual, LinearCompuMethod)
        assert isinstance(actual, LinearCompuMethod)
        self.assertEqual(expected.physical_type, actual.physical_type)
        self.assertEqual(expected.internal_type, actual.internal_type)
        self.assertEqual(expected.segment.offset, actual.segment.offset)
        self.assertEqual(expected.segment.factor, actual.segment.factor)
        self.assertEqual(expected.segment.denominator, actual.segment.denominator)

    def test_write_odx(self) -> None:
        self.maxDiff = None
        dlc_tpl = self.jinja_env.get_template("macros/printCompuMethod.xml.jinja2")
        module = dlc_tpl.make_module()

        actual_xml = module.printCompuMethod(self.linear_compumethod)  # type: ignore[attr-defined]

        expected_xml = self.linear_compumethod_xml

        # We ignore spaces
        def remove_spaces(string: str) -> str:
            return "".join(string.split())

        self.assertEqual(remove_spaces(actual_xml), remove_spaces(expected_xml))

    def test_linear_compu_method_type_denom_not_one(self) -> None:
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="0",
                            value_type=DataType.A_INT32,
                            interval_type=IntervalType.INFINITE),
                        upper_limit=Limit(
                            value_raw="0",
                            value_type=DataType.A_INT32,
                            interval_type=IntervalType.INFINITE),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[0, 1],
                            denominators=[3600],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)

        self.assertEqual(compu_method.convert_physical_to_internal(2), 7200)
        self.assertEqual(compu_method.convert_internal_to_physical(7200), 2)

    def test_linear_compu_method_type_int_int(self) -> None:
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=None,
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[1, 3],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)

        self.assertEqual(compu_method.convert_internal_to_physical(4), 13)
        self.assertEqual(compu_method.convert_internal_to_physical(0), 1)
        self.assertEqual(compu_method.convert_internal_to_physical(-2), -5)

        self.assertEqual(compu_method.convert_physical_to_internal(13), 4)
        self.assertEqual(compu_method.convert_physical_to_internal(1), 0)
        self.assertEqual(compu_method.convert_physical_to_internal(-5), -2)

    def test_linear_compu_method_type_int_float(self) -> None:
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=None,
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[1, 3],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_FLOAT32)

        self.assertTrue(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value("123"))
        self.assertFalse(compu_method.is_valid_internal_value(1.2345))

        self.assertTrue(compu_method.is_valid_physical_value(1.2345))
        self.assertTrue(compu_method.is_valid_physical_value(123))
        self.assertFalse(compu_method.is_valid_physical_value("123"))

    def test_linear_compu_method_type_float_int(self) -> None:
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=None,
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[1, 3],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_INT32)
        self.assertTrue(compu_method.is_valid_internal_value(1.2345))
        self.assertTrue(compu_method.is_valid_internal_value(123))
        self.assertFalse(compu_method.is_valid_internal_value("123"))

        self.assertTrue(compu_method.is_valid_physical_value(123))
        self.assertFalse(compu_method.is_valid_physical_value("123"))
        self.assertFalse(compu_method.is_valid_physical_value(1.2345))

    def test_linear_compu_method_type_string(self) -> None:
        with self.assertRaises(OdxError):
            LinearCompuMethod(
                category=CompuCategory.LINEAR,
                compu_internal_to_phys=CompuInternalToPhys(
                    compu_scales=[
                        CompuScale(
                            short_label=None,
                            description=None,
                            lower_limit=None,
                            upper_limit=None,
                            compu_inverse_value=None,
                            compu_const=None,
                            compu_rational_coeffs=CompuRationalCoeffs(
                                value_type=DataType.A_INT32,
                                numerators=[1, 3],
                                denominators=[1],
                            ),
                            domain_type=DataType.A_INT32,
                            range_type=DataType.A_INT32),
                    ],
                    prog_code=None,
                    compu_default_value=None),
                compu_phys_to_internal=None,
                internal_type=DataType.A_ASCIISTRING,
                physical_type=DataType.A_UNICODE2STRING)

    def test_linear_compu_method_limits(self) -> None:
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="2", value_type=DataType.A_INT32, interval_type=None),
                        upper_limit=Limit(
                            value_raw="15", value_type=DataType.A_INT32, interval_type=None),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[1, 5],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)

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

    def test_linear_compu_method_physical_limits(self) -> None:
        # Define decoding function: f: (2, 15] -> [-74, -14], f(x) = -5*x + 1
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="2",
                            value_type=DataType.A_INT32,
                            interval_type=IntervalType.OPEN),
                        upper_limit=Limit(
                            value_raw="15", value_type=DataType.A_INT32, interval_type=None),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[1, -5],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)

        assert compu_method.segment.internal_lower_limit is not None
        assert compu_method.segment.internal_upper_limit is not None
        assert compu_method.segment.physical_lower_limit is not None
        assert compu_method.segment.physical_upper_limit is not None

        self.assertEqual(
            compu_method.segment.internal_lower_limit,
            Limit(value_raw="2", value_type=DataType.A_INT32, interval_type=IntervalType.OPEN))
        self.assertEqual(compu_method.segment.internal_upper_limit,
                         Limit(value_raw="15", value_type=DataType.A_INT32, interval_type=None))
        self.assertEqual(compu_method.segment.internal_upper_limit.interval_type, None)

        self.assertEqual(compu_method.segment.physical_lower_limit,
                         Limit(value_raw="-74", value_type=DataType.A_INT32, interval_type=None))
        self.assertEqual(
            compu_method.segment.physical_upper_limit,
            Limit(value_raw="-9", value_type=DataType.A_INT32, interval_type=IntervalType.OPEN))

        self.assertFalse(compu_method.segment.internal_lower_limit.complies_to_lower(2))
        self.assertTrue(compu_method.segment.internal_lower_limit.complies_to_lower(3))
        self.assertTrue(compu_method.segment.internal_upper_limit.complies_to_upper(15))
        self.assertFalse(compu_method.segment.internal_upper_limit.complies_to_upper(16))

        self.assertFalse(compu_method.segment.physical_lower_limit.complies_to_lower(-75))
        self.assertTrue(compu_method.segment.physical_lower_limit.complies_to_lower(-74))
        self.assertTrue(compu_method.segment.physical_upper_limit.complies_to_upper(-10))
        self.assertFalse(compu_method.segment.physical_upper_limit.complies_to_upper(-9))

        self.assertTrue(compu_method.is_valid_internal_value(3))
        self.assertTrue(compu_method.is_valid_internal_value(15))
        self.assertFalse(compu_method.is_valid_internal_value(2))
        self.assertFalse(compu_method.is_valid_internal_value(16))

        self.assertFalse(compu_method.is_valid_physical_value(-75))
        self.assertTrue(compu_method.is_valid_physical_value(-74))
        self.assertTrue(compu_method.is_valid_physical_value(-14))
        self.assertTrue(compu_method.is_valid_physical_value(-10))
        self.assertFalse(compu_method.is_valid_physical_value(-9))


class TestCompuCodeCompuMethod(unittest.TestCase):

    def test_compu_code_compu_method(self) -> None:
        compu_method = CompuCodeCompuMethod(
            category=CompuCategory.COMPUCODE,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[],
                prog_code=ProgCode(
                    code_file="nice_computation.java",
                    syntax="JAVA",
                    revision="1.0",
                    encryption=None,
                    entrypoint=None,
                    library_refs=[]),
                compu_default_value=None),
            compu_phys_to_internal=CompuPhysToInternal(
                compu_scales=[],
                prog_code=ProgCode(
                    code_file="nice_inverse_computation.java",
                    syntax="JAVA",
                    revision="1.0",
                    encryption=None,
                    entrypoint=None,
                    library_refs=[]),
                compu_default_value=None),
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32)

        # COMPUCODE compu methods can only be used from Java projects
        # (i.e., not odxtools)
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(1)
        with self.assertRaises(EncodeError):
            compu_method.convert_physical_to_internal(2)


class TestRatFuncCompuMethod(unittest.TestCase):

    def test_rat_func_compu_method(self) -> None:
        compu_method = RatFuncCompuMethod(
            category=CompuCategory.RAT_FUNC,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="2",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="3",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # f(x) = 3.14*(2*x^2 + 4x + 6) / 3.14
                            numerators=[3.14 * 6, 3.14 * 4, 3.14 * 2],
                            denominators=[3.14],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32)

        self.assertTrue(abs(float(compu_method.convert_internal_to_physical(2.5)) - 28.5) < 1e-5)

        # out of range
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(3.01)
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(1.99)

        # if the inverse function is not explicitly specified,
        # inversion is not allowed!
        with self.assertRaises(EncodeError):
            compu_method.convert_physical_to_internal(2.5)

    def test_rat_func_compu_method_with_inverse(self) -> None:
        compu_method = RatFuncCompuMethod(
            category=CompuCategory.RAT_FUNC,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="2",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="3",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # f(x) = x^2
                            numerators=[0, 0, 1],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=CompuPhysToInternal(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="4",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="9",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # first three terms of Taylor expansion of
                            # f(x) = sqrt(x) at evaluation point 1
                            numerators=[2.72 * 3 / 8, 2.72 * 3 / 4, 2.72 * -1 / 8],
                            denominators=[2.72],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32)

        self.assertEqual(compu_method.convert_internal_to_physical(2), 4)
        self.assertEqual(compu_method.convert_internal_to_physical(2.5), 6.25)
        self.assertTrue(abs(float(compu_method.convert_internal_to_physical(3)) - 9) < 1e-8)

        # note that the inverse values are pretty inaccurate because
        # the Taylor series was cut off way quite early.
        self.assertTrue(abs(float(compu_method.convert_physical_to_internal(4)) - 1.375) < 1e-4)
        self.assertTrue(
            abs(float(compu_method.convert_physical_to_internal(6.25)) - 0.17969) < 1e-4)
        self.assertEqual(compu_method.convert_physical_to_internal(9), -3)

        # ensure that we stay in bounds
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(3.99)
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(9.01)


class TestScaleRatFuncCompuMethod(unittest.TestCase):

    def test_scale_rat_func_compu_method(self) -> None:
        compu_method = ScaleRatFuncCompuMethod(
            category=CompuCategory.SCALE_RAT_FUNC,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="2",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="3",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # f(x) = 3.14*(2*x^2 + 4x + 6) / 3.14
                            numerators=[3.14 * 6, 3.14 * 4, 3.14 * 2],
                            denominators=[3.14],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32)

        self.assertTrue(abs(float(compu_method.convert_internal_to_physical(2.5)) - 28.5) < 1e-5)

        # out of range
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(3.01)
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(1.99)

        # if the inverse function is not explicitly specified,
        # inversion is not allowed!
        with self.assertRaises(EncodeError):
            compu_method.convert_physical_to_internal(2.5)

    def test_scale_rat_func_compu_method_with_inverse(self) -> None:
        compu_method = ScaleRatFuncCompuMethod(
            category=CompuCategory.SCALE_RAT_FUNC,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="2",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="3",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # f(x) = x^2
                            numerators=[0, 0, 1],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="4",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="5",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # f(x) = 1.38e-23*(3*x + 10)/1.38e-23
                            numerators=[1.38e-23 * 10, 1.38e-23 * 3],
                            denominators=[1.38e-23],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=CompuPhysToInternal(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="4",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="9",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # first three terms of Taylor expansion of
                            # f(x) = sqrt(x) at evaluation point 1
                            numerators=[2.72 * 3 / 8, 2.72 * 3 / 4, 2.72 * -1 / 8],
                            denominators=[2.72],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="22",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        upper_limit=Limit(
                            value_raw="25",
                            value_type=DataType.A_FLOAT32,
                            interval_type=IntervalType.CLOSED),
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_FLOAT32,
                            # f(x) = (x - 10)/3
                            numerators=[-10, 1],
                            denominators=[3],
                        ),
                        domain_type=DataType.A_FLOAT32,
                        range_type=DataType.A_FLOAT32),
                ],
                prog_code=None,
                compu_default_value=None),
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32)

        self.assertEqual(compu_method.convert_internal_to_physical(2), 4)
        self.assertEqual(compu_method.convert_internal_to_physical(2.5), 6.25)
        self.assertTrue(abs(float(compu_method.convert_internal_to_physical(3)) - 9) < 1e-8)

        self.assertTrue(abs(float(compu_method.convert_internal_to_physical(4)) - 22) < 1e-8)
        self.assertTrue(abs(float(compu_method.convert_physical_to_internal(22)) - 4) < 1e-8)

        # note that the inverse values are pretty inaccurate because
        # the Taylor series was cut off way quite early.
        self.assertTrue(abs(float(compu_method.convert_physical_to_internal(4)) - 1.375) < 1e-4)
        self.assertTrue(
            abs(float(compu_method.convert_physical_to_internal(6.25)) - 0.17969) < 1e-4)
        self.assertEqual(compu_method.convert_physical_to_internal(9), -3)

        # make sure that we stay in bounds
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(3.99)
        with self.assertRaises(DecodeError):
            compu_method.convert_internal_to_physical(9.01)


class TestTabIntpCompuMethod(unittest.TestCase):

    def setUp(self) -> None:
        """Prepares the jinja environment and the sample tab-intp compumethod"""

        def _get_jinja_environment() -> jinja2.environment.Environment:
            __module_filename = inspect.getsourcefile(odxtools)
            assert isinstance(__module_filename, str)
            templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])

            jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))

            # allows to put XML attributes on a separate line while it is
            # collapsed with the previous line in the rendering
            jinja_env.filters["odxtools_collapse_xml_attribute"] = (lambda x: " " + x.strip()
                                                                    if x.strip() else "")

            jinja_env.globals["getattr"] = getattr
            jinja_env.globals["hasattr"] = hasattr
            return jinja_env

        self.jinja_env = _get_jinja_environment()

        self.tab_intp_compumethod = TabIntpCompuMethod(
            category=CompuCategory.TAB_INTP,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="0", value_type=DataType.A_INT32, interval_type=None),
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=CompuConst(v="-1", vt=None, data_type=DataType.A_INT32),
                        compu_rational_coeffs=None,
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="10", value_type=DataType.A_INT32, interval_type=None),
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=CompuConst(v="1", vt=None, data_type=DataType.A_INT32),
                        compu_rational_coeffs=None,
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=Limit(
                            value_raw="30", value_type=DataType.A_INT32, interval_type=None),
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=CompuConst(v="2", vt=None, data_type=DataType.A_INT32),
                        compu_rational_coeffs=None,
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_FLOAT32,
        )

        self.tab_intp_compumethod_xml = f"""
        <COMPU-METHOD>
            <CATEGORY>TAB-INTP</CATEGORY>
            <COMPU-INTERNAL-TO-PHYS>
                <COMPU-SCALES>
                    <COMPU-SCALE>
                        <LOWER-LIMIT>{self.tab_intp_compumethod.internal_points[0]}</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>{self.tab_intp_compumethod.physical_points[0]}</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                    <COMPU-SCALE>
                        <LOWER-LIMIT>{self.tab_intp_compumethod.internal_points[1]}</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>{self.tab_intp_compumethod.physical_points[1]}</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                    <COMPU-SCALE>
                        <LOWER-LIMIT>{self.tab_intp_compumethod.internal_points[2]}</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>{self.tab_intp_compumethod.physical_points[2]}</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                </COMPU-SCALES>
            </COMPU-INTERNAL-TO-PHYS>
        </COMPU-METHOD>
        """

    def test_tabintp_convert_type_int_float(self) -> None:
        method = self.tab_intp_compumethod

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

    def test_read_odx(self) -> None:
        expected = self.tab_intp_compumethod

        et_element = ElementTree.fromstring(self.tab_intp_compumethod_xml)
        actual = create_any_compu_method_from_et(
            et_element,
            doc_frags,
            internal_type=expected.internal_type,
            physical_type=expected.physical_type)
        self.assertIsInstance(actual, TabIntpCompuMethod)
        assert isinstance(expected, TabIntpCompuMethod)
        assert isinstance(actual, TabIntpCompuMethod)
        self.assertEqual(expected.physical_type, actual.physical_type)
        self.assertEqual(expected.internal_type, actual.internal_type)
        self.assertEqual(expected.internal_points, actual.internal_points)
        self.assertEqual(expected.physical_points, actual.physical_points)

    def test_write_odx(self) -> None:
        dlc_tpl = self.jinja_env.get_template("macros/printCompuMethod.xml.jinja2")
        module = dlc_tpl.make_module()

        actual_xml = module.printCompuMethod(  # type: ignore[attr-defined]
            self.tab_intp_compumethod)

        expected_xml = self.tab_intp_compumethod_xml

        # We ignore spaces
        def remove_spaces(string: str) -> str:
            return "".join(string.split())

        self.assertEqual(remove_spaces(actual_xml), remove_spaces(expected_xml))


if __name__ == "__main__":
    unittest.main()
