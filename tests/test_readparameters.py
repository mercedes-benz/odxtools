# SPDX-License-Identifier: MIT
import unittest
from xml.etree import ElementTree

from odxtools.odxlink import OdxDocFragment
from odxtools.odxtypes import DataType
from odxtools.parameters.createanyparameter import create_any_parameter_from_et
from odxtools.parameters.nrcconstparameter import NrcConstParameter

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestReadNrcParam(unittest.TestCase):

    def test_create_nrcconst_from_et(self) -> None:
        ODX = """
        <PARAM SEMANTIC="SUBFUNCTION-ID" xsi:type="NRC-CONST" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <SHORT-NAME>NR_identifier</SHORT-NAME>
            <LONG-NAME>Identifier for the negative response</LONG-NAME>
            <BYTE-POSITION>0</BYTE-POSITION>
            <CODED-VALUES>
                <CODED-VALUE>16</CODED-VALUE>
                <CODED-VALUE>10</CODED-VALUE>
            </CODED-VALUES>
            <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" xsi:type="STANDARD-LENGTH-TYPE">
                <BIT-LENGTH>8</BIT-LENGTH>
            </DIAG-CODED-TYPE>
        </PARAM>
        """
        root = ElementTree.fromstring(ODX)
        param = create_any_parameter_from_et(root, doc_frags=doc_frags)

        self.assertIsInstance(param, NrcConstParameter)
        assert isinstance(param, NrcConstParameter)
        self.assertEqual("SUBFUNCTION-ID", param.semantic)
        self.assertEqual("NR_identifier", param.short_name)
        self.assertEqual("Identifier for the negative response", param.long_name)
        self.assertEqual([16, 10], param.coded_values)
        self.assertEqual(DataType.A_UINT32, param.diag_coded_type.base_data_type)
        self.assertEqual(8, param.diag_coded_type.get_static_bit_length())
