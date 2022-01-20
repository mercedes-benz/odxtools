# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


import unittest

from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.compumethods import LinearCompuMethod
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.parameters import CodedConstParameter, ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.structures import Request

class TestEncodeRequest(unittest.TestCase):
    def test_encode_coded_const_infer_order(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        param1 = CodedConstParameter(
            "coded_const_parameter", diag_coded_type, coded_value=0x7d, byte_position=0)
        param2 = CodedConstParameter(
            "coded_const_parameter", diag_coded_type, coded_value=0xab)
        req = Request("request_id", "request_sn", [param1, param2])
        self.assertEqual(req.encode(), bytearray([0x7d, 0xab]))

    def test_encode_coded_const_rerder(self):
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
        dop = DataObjectProperty("dop-id", "example dop", diag_coded_type,
                                 physical_type=PhysicalType("A_UINT32"), compu_method=compu_method)
        param1 = ValueParameter("linear_value_parameter", dop=dop)
        req = Request("request_id", "request_sn", [param1])

        # Missing mandatory parameter.
        with self.assertRaises(TypeError) as cm:
            req.encode()

        self.assertEqual(
            req.encode(linear_value_parameter=14),
            bytearray([0x3])  # encode(14) = (14-8)/2 = 3
        )


if __name__ == '__main__':
    unittest.main()
