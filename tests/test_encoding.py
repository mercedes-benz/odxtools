# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


import unittest

from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.compumethods import LinearCompuMethod
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.exceptions import EncodeError
from odxtools.parameters import CodedConstParameter, ValueParameter, NrcConstParameter
from odxtools.physicaltype import PhysicalType
from odxtools.structures import Request, Response
from odxtools.odxlink import OdxLinkId, OdxLinkRef, OdxLinkDatabase, OdxDocFragment

doc_frag = OdxDocFragment("UnitTest", "WinneThePoh")

class TestEncodeRequest(unittest.TestCase):
    def test_encode_coded_const_infer_order(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        param1 = CodedConstParameter(
            "coded_const_parameter", diag_coded_type, coded_value=0x7d, byte_position=0)
        param2 = CodedConstParameter(
            "coded_const_parameter", diag_coded_type, coded_value=0xab)
        req = Request("request_id", "request_sn", [param1, param2])
        self.assertEqual(req.encode(), bytearray([0x7d, 0xab]))

    def test_encode_coded_const_reorder(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        param1 = CodedConstParameter(
            "param1", diag_coded_type, coded_value=0x34, byte_position=1)
        param2 = CodedConstParameter(
            "param2", diag_coded_type, coded_value=0x12, byte_position=0)
        req = Request("request_id", "request_sn", [param1, param2])
        self.assertEqual(req.encode(), bytearray([0x12, 0x34]))

    def test_encode_linear(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        # This CompuMethod represents the linear function: decode(x) = 2*x + 8 and encode(x) = (x-8)/2
        compu_method = LinearCompuMethod(8, 2, "A_UINT32", "A_UINT32")
        dop = DataObjectProperty(OdxLinkId("dop-id", doc_frag), "example dop", diag_coded_type,
                                 physical_type=PhysicalType("A_UINT32"), compu_method=compu_method)
        param1 = ValueParameter("linear_value_parameter",
                                dop=dop)
        req = Request("request_id", "request_sn", [param1])

        # Missing mandatory parameter.
        with self.assertRaises(TypeError) as cm:
            req.encode()

        self.assertEqual(
            req.encode(linear_value_parameter=14),
            bytearray([0x3])  # encode(14) = (14-8)/2 = 3
        )

    def test_encode_nrc_const(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        param1 = CodedConstParameter(
            "param1", diag_coded_type, coded_value=0x12, byte_position=0)
        param2 = NrcConstParameter(
            "param2", diag_coded_type, coded_values=[0x34, 0xab], byte_position=1)
        resp = Response("response_id", "response_sn", [param1, param2])
        self.assertEqual(resp.encode(), bytearray([0x12, 0x34]))
        self.assertEqual(resp.encode(param2=0xab), bytearray([0x12, 0xab]))
        self.assertRaises(EncodeError, resp.encode, param2=0xef)

    def test_encode_overlapping(self):
        uint24 = StandardLengthType("A_UINT32", 24)
        uint8 = StandardLengthType("A_UINT32", 8)
        param1 = CodedConstParameter(
            "code", uint24, coded_value=0x123456)
        param2 = CodedConstParameter(
            "part1", uint8, coded_value=0x23, byte_position=0, bit_position=4)
        param3 = CodedConstParameter(
            "part2", uint8, coded_value=0x45, byte_position=1, bit_position=4)
        req = Request("request_id", "request_sn", [param1, param2, param3])
        self.assertEqual(req.encode(), bytearray([0x12, 0x34, 0x56]))
        self.assertEqual(req.bit_length, 24)

    def test_issue_70(self):
        self.skipTest("Not fixed yet")
        # see https://github.com/mercedes-benz/odxtools/issues/70
        # make sure overlapping params don't cause this function to go crazy
        uint2 = StandardLengthType("A_UINT32", 2)
        uint1 = StandardLengthType("A_UINT32", 1)
        params = [
            CodedConstParameter("p1", uint2, bit_position=0, coded_value=0),
            CodedConstParameter("p2", uint2, bit_position=2, coded_value=0),
            CodedConstParameter("p3", uint2, bit_position=3, coded_value=0),
            CodedConstParameter("p4", uint1, bit_position=5, coded_value=0),
            CodedConstParameter("p5", uint1, bit_position=6, coded_value=0),
            CodedConstParameter("p6", uint1, bit_position=7, coded_value=0),
        ]
        req = Request("request_id", "request_sn", params)
        self.assertTrue(req._BasicStructure__message_format_lines())

if __name__ == '__main__':
    unittest.main()
