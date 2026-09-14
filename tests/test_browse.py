# SPDX-License-Identifier: MIT
import argparse
import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch

from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagnostictroublecode import DiagnosticTroubleCode
from odxtools.dtcdop import DtcDop
from odxtools.environmentdatadescription import EnvironmentDataDescription
from odxtools.exceptions import OdxError
from odxtools.field import Field
from odxtools.loadfile import load_pdx_file
from odxtools.multiplexer import Multiplexer
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkId
from odxtools.odxtypes import DataType
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.text import Text

browse: ModuleType | None
try:
    import odxtools.cli.browse as browse
except ImportError:
    browse = None

odxdb = load_pdx_file("./examples/somersault.pdx")


def _make_odx_link_id(local_id: str) -> OdxLinkId:
    return OdxLinkId(
        local_id=local_id,
        doc_fragments=(OdxDocFragment(doc_name="test", doc_type=DocType.LAYER),),
    )


@unittest.skipIf(browse is None, "importing the browse tool failed")
class TestBrowseTool(unittest.TestCase):

    def test_convert_string_to_odx_type(self) -> None:
        assert browse is not None
        self.assertEqual(browse._convert_string_to_odx_type("0x10", DataType.A_UINT32), 16)
        self.assertEqual(browse._convert_string_to_odx_type("42", DataType.A_UINT32), 42)
        self.assertEqual(
            browse._convert_string_to_odx_type("01 02 03", DataType.A_BYTEFIELD),
            bytes([1, 2, 3]),
        )
        self.assertEqual(browse._convert_string_to_odx_type("-5", DataType.A_INT32), -5)
        self.assertEqual(browse._convert_string_to_odx_type("3.14", DataType.A_FLOAT32), 3.14)

    def test_convert_string_to_bytes(self) -> None:
        assert browse is not None
        self.assertEqual(browse._convert_string_to_bytes("01 02 03"), bytes([1, 2, 3]))
        self.assertEqual(browse._convert_string_to_bytes("1234"), bytes([0x12, 0x34]))
        self.assertEqual(browse._convert_string_to_bytes(""), b"")

    def test_validate_chosen_value_dtc_dop(self) -> None:
        assert browse is not None
        dtc = DiagnosticTroubleCode(
            odx_id=_make_odx_link_id("DTC.test"),
            short_name="test_dtc",
            trouble_code=0x123456,
            text=Text.from_string("Test DTC"),
            display_trouble_code="DTC_123456",
        )
        dop = MagicMock(spec=DtcDop)
        dop.dtcs = [dtc]

        self.assertTrue(browse._validate_chosen_value("test_dtc", dop, True))
        self.assertTrue(browse._validate_chosen_value("DTC_123456", dop, True))
        self.assertTrue(browse._validate_chosen_value(0x123456, dop, True))
        self.assertTrue(browse._validate_chosen_value("0x123456", dop, True))
        self.assertTrue(browse._validate_chosen_value(dtc, dop, True))
        self.assertTrue(browse._validate_chosen_value(None, dop, False))
        self.assertFalse(browse._validate_chosen_value("unknown", dop, True))
        self.assertFalse(browse._validate_chosen_value("not_a_number", dop, True))

        # numeric trouble code that is not in the list of DTCs
        self.assertFalse(browse._validate_chosen_value(0xFFFFFF, dop, True))
        self.assertFalse(browse._validate_chosen_value("0xFFFFFF", dop, True))

    def test_validate_chosen_value_data_object_property(self) -> None:
        assert browse is not None
        dop = MagicMock(spec=DataObjectProperty)
        dop.physical_type = MagicMock()
        dop.physical_type.base_data_type = DataType.A_UINT32
        dop.is_valid_physical_value.return_value = True

        self.assertTrue(browse._validate_chosen_value("42", dop, True))
        dop.is_valid_physical_value.return_value = False
        self.assertFalse(browse._validate_chosen_value("42", dop, True))
        self.assertTrue(browse._validate_chosen_value(None, dop, False))

        dop.physical_type.base_data_type = DataType.A_BYTEFIELD
        dop.is_valid_physical_value.return_value = True
        self.assertTrue(browse._validate_chosen_value("01 02", dop, True))

        # non-string input values are validated directly
        dop.is_valid_physical_value.return_value = True
        self.assertTrue(browse._validate_chosen_value(42, dop, True))
        dop.is_valid_physical_value.return_value = False
        self.assertFalse(browse._validate_chosen_value(42, dop, True))

        # invalid string values are rejected
        dop.physical_type.base_data_type = DataType.A_UINT32
        dop.is_valid_physical_value.return_value = True
        self.assertFalse(browse._validate_chosen_value("not_a_number", dop, True))

    def test_validate_chosen_value_unsupported_dop(self) -> None:
        assert browse is not None
        dop = MagicMock()
        dop.__class__.__name__ = "UnsupportedDop"
        with self.assertRaises(NotImplementedError):
            browse._validate_chosen_value("foo", dop, True)

    def test_prompt_primitive_parameter_value_no_physical_type(self) -> None:
        assert browse is not None
        param = MagicMock(spec=ValueParameter)
        param.short_name = "no_phys_param"
        param.physical_type = None

        with self.assertRaises(OdxError):
            browse.prompt_primitive_parameter_value(param)

    def test_prompt_all_parameter_values_unsupported_dops(self) -> None:
        assert browse is not None

        for dop_type, dop in [
            ("Field", MagicMock(spec=Field)),
            ("Multiplexer", MagicMock(spec=Multiplexer)),
            ("EnvironmentDataDescription", MagicMock(spec=EnvironmentDataDescription)),
        ]:
            with self.subTest(dop_type=dop_type):
                dop.short_name = f"{dop_type.lower()}_dop"
                param = MagicMock(spec=ValueParameter)
                param.short_name = f"{dop_type.lower()}_param"
                param.dop = dop
                param.is_settable = True

                with self.assertRaises(OdxError):
                    browse.prompt_all_parameter_values([param])

    def test_encode_message_interactively_non_tty(self) -> None:
        assert browse is not None
        codec = MagicMock()
        with patch.object(browse.sys, "__stdin__", None):
            with self.assertRaises(SystemError):
                browse.encode_message_interactively(codec)

    def test_browse_non_tty(self) -> None:
        assert browse is not None
        with patch.object(browse.sys, "__stdin__", None):
            with self.assertRaises(SystemError):
                browse.browse(odxdb)

    def test_add_subparser(self) -> None:
        assert browse is not None
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        browse.add_subparser(subparsers)

        # verify that the "browse" subparser was added
        with self.assertRaises(SystemExit):
            parser.parse_args(["browse", "--help"])

    @patch("odxtools.cli.browse.browse")
    def test_run(self, mock_browse: MagicMock) -> None:
        assert browse is not None
        args = argparse.Namespace(pdx_file="./examples/somersault.pdx")
        browse.run(args)
        mock_browse.assert_called_once()


if __name__ == "__main__":
    unittest.main()
