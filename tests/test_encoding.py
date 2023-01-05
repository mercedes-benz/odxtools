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

doc_frags = [ OdxDocFragment("UnitTest", "WinneThePoh") ]

class TestEncodeRequest(unittest.TestCase):
    def test_encode_coded_const_infer_order(self):
        diag_coded_type = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        param1 = CodedConstParameter(short_name="coded_const_parameter",
                                     diag_coded_type=diag_coded_type,
                                     coded_value=0x7d,
                                     byte_position=0)
        param2 = CodedConstParameter(short_name="coded_const_parameter",
                                     diag_coded_type=diag_coded_type,
                                     coded_value=0xab)
        req = Request(odx_id=OdxLinkId("request_id", doc_frags),
                      short_name="request_sn",
                      parameters=[param1, param2])
        self.assertEqual(req.encode(), bytearray([0x7d, 0xab]))

    def test_encode_coded_const_reorder(self):
        diag_coded_type = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        param1 = CodedConstParameter(short_name="param1",
                                     diag_coded_type=diag_coded_type,
                                     coded_value=0x34,
                                     byte_position=1)
        param2 = CodedConstParameter(short_name="param2",
                                     diag_coded_type=diag_coded_type,
                                     coded_value=0x12,
                                     byte_position=0)
        req = Request(odx_id=OdxLinkId("request_id", doc_frags),
                      short_name="request_sn",
                      parameters=[param1, param2])
        self.assertEqual(req.encode(), bytearray([0x12, 0x34]))

    def test_encode_linear(self):
        diag_coded_type = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        # This CompuMethod represents the linear function: decode(x) = 2*x + 8 and encode(x) = (x-8)/2
        compu_method = LinearCompuMethod(offset=8,
                                         factor=2,
                                         internal_type="A_UINT32",
                                         physical_type="A_UINT32")
        dop = DataObjectProperty(odx_id=OdxLinkId("dop-odx_id", doc_frags),
                                 short_name="example dop",
                                 diag_coded_type=diag_coded_type,
                                 physical_type=PhysicalType("A_UINT32"),
                                 compu_method=compu_method)
        param1 = ValueParameter(short_name="linear_value_parameter",
                                dop=dop)
        req = Request(odx_id=OdxLinkId("request_id", doc_frags),
                      short_name="request_sn",
                      parameters=[param1])

        # Missing mandatory parameter.
        with self.assertRaises(TypeError) as cm:
            req.encode()

        self.assertEqual(
            req.encode(linear_value_parameter=14),
            bytearray([0x3])  # encode(14) = (14-8)/2 = 3
        )

    def test_encode_nrc_const(self):
        diag_coded_type = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        param1 = CodedConstParameter(short_name="param1",
                                     diag_coded_type=diag_coded_type,
                                     coded_value=0x12,
                                     byte_position=0)
        param2 = NrcConstParameter(short_name="param2",
                                   diag_coded_type=diag_coded_type,
                                   coded_values=[0x34, 0xab],
                                   byte_position=1)
        resp = Response(odx_id=OdxLinkId("response_id", doc_frags),
                        short_name= "response_sn",
                        parameters=[param1, param2])
        self.assertEqual(resp.encode(), bytearray([0x12, 0x34]))
        self.assertEqual(resp.encode(param2=0xab), bytearray([0x12, 0xab]))
        self.assertRaises(EncodeError, resp.encode, param2=0xef)

    def test_encode_overlapping(self):
        uint24 = StandardLengthType(base_data_type="A_UINT32", bit_length=24)
        uint8 = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        param1 = CodedConstParameter(short_name="code",
                                     diag_coded_type=uint24,
                                     coded_value=0x123456)
        param2 = CodedConstParameter(short_name="part1",
                                     diag_coded_type=uint8,
                                     coded_value=0x23,
                                     byte_position=0,
                                     bit_position=4)
        param3 = CodedConstParameter(short_name="part2",
                                     diag_coded_type=uint8,
                                     coded_value=0x45,
                                     byte_position=1,
                                     bit_position=4)
        req = Request(odx_id=OdxLinkId("request_id", doc_frags),
                      short_name="request_sn",
                      parameters=[param1, param2, param3])
        self.assertEqual(req.encode(), bytearray([0x12, 0x34, 0x56]))
        self.assertEqual(req.bit_length, 24)

    def test_issue_70(self):
        self.skipTest("Not fixed yet")
        # see https://github.com/mercedes-benz/odxtools/issues/70
        # make sure overlapping params don't cause this function to go crazy
        uint2 = StandardLengthType(base_data_type="A_UINT32", bit_length=2)
        uint1 = StandardLengthType(base_data_type="A_UINT32", bit_length=1)
        params = [
            CodedConstParameter(short_name="p1",
                                diag_coded_type=uint2,
                                bit_position=0,
                                coded_value=0),
            CodedConstParameter(short_name="p2",
                                diag_coded_type=uint2,
                                bit_position=2,
                                coded_value=0),
            CodedConstParameter(short_name="p3",
                                diag_coded_type=uint2,
                                bit_position=3,
                                coded_value=0),
            CodedConstParameter(short_name="p4",
                                diag_coded_type=uint1,
                                bit_position=5,
                                coded_value=0),
            CodedConstParameter(short_name="p5",
                                diag_coded_type=uint1,
                                bit_position=6,
                                coded_value=0),
            CodedConstParameter(short_name="p6",
                                diag_coded_type=uint1,
                                bit_position=7,
                                coded_value=0),
        ]
        req = Request(odx_id=OdxLinkRef("request_id", doc_frags),
                      short_name="request_sn",
                      parameters=params)
        self.assertTrue(req._BasicStructure__message_format_lines())

if __name__ == '__main__':
    unittest.main()
