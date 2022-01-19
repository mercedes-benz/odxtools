# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from odxtools.endofpdufield import EndOfPduField
from odxtools.dataobjectproperty import DataObjectProperty, DiagnosticTroubleCode, DtcDop
from odxtools.compumethods import IdenticalCompuMethod, LinearCompuMethod
from odxtools.message import Message
import unittest

from odxtools.diagcodedtypes import StandardLengthType
from odxtools.parameters import CodedConstParameter, MatchingRequestParameter, ValueParameter
from odxtools.structures import Request, Response, Structure
from odxtools.service import DiagService
from odxtools.diaglayer import DiagLayer


class TestIdentifyingService(unittest.TestCase):
    def test_prefix_tree_construction(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        diag_coded_type_2 = StandardLengthType("A_UINT32", 16)
        req_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x7d, byte_position=0)
        req_param2 = CodedConstParameter(
            "coded_const_parameter_2", diag_coded_type, coded_value=0xab, byte_position=1)
        req = Request("request_id", "request_sn", [req_param1, req_param2])
        id_lookup = {req.id: req}
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[],
                              negative_responses=[])

        req2_param2 = CodedConstParameter(
            "coded_const_parameter_3", diag_coded_type_2, coded_value=0xcde)
        req2 = Request("request_id2", "request_sn2", [req_param1, req2_param2])
        id_lookup[req2.id] = req2

        resp2_param2 = CodedConstParameter(
            "coded_const_parameter_4", diag_coded_type_2, coded_value=0xc86)
        resp2 = Response("response_id2", "response_sn2",
                         [req_param1, resp2_param2])
        id_lookup[resp2.id] = resp2

        service2 = DiagService(id="service_id2",
                               short_name="service_sn2",
                               request=req2.id,
                               positive_responses=[resp2.id],
                               negative_responses=[])

        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service, service2],
                               requests=[req, req2],
                               positive_responses=[resp2],
                               id_lookup=id_lookup)

        self.assertEqual(diag_layer._build_coded_prefix_tree(), {
                         0x7d: {
                             0xab: {-1: [service]},
                             0xc: {
                                 0xde: {-1: [service2]},
                                 0x86: {-1: [service2]}
                             }}})


class TestDecoding(unittest.TestCase):
    def test_decode_request_const(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        req_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x7d, byte_position=0)
        req_param2 = CodedConstParameter(
            "coded_const_parameter_2", diag_coded_type, coded_value=0xab, byte_position=1)
        req = Request("request_id", "request_sn", [req_param1, req_param2])

        id_lookup = {req.id: req}
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[],
                              negative_responses=[])
        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service],
                               requests=[req],
                               positive_responses=[],
                               id_lookup=id_lookup)

        coded_message = bytes([0x7d, 0xab])
        expected_message = Message(coded_message, service, req, param_dict={"SID": 0x7d,
                                                                            "coded_const_parameter_2": 0xab})
        decoded_message = diag_layer.decode(coded_message)[0]
        
        self.assertEqual(expected_message.coded_message,
                         decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.structure, decoded_message.structure)
        self.assertEqual(expected_message.param_dict,
                         decoded_message.param_dict)

    def test_decode_request_const_byte_position(self):
        """Test decoding of parameter
        Test if the decoding works if the byte position of the second parameter
        must be inferred from the order in the surrounding structure."""
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        req_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x12, byte_position=0)
        req_param2 = CodedConstParameter(
            "coded_const_parameter_2", diag_coded_type, coded_value=0x56, byte_position=2)
        req_param3 = CodedConstParameter(
            "coded_const_parameter_3", diag_coded_type, coded_value=0x34, byte_position=1)
        req_param4 = CodedConstParameter(
            "coded_const_parameter_4", diag_coded_type, coded_value=0x78)
        req = Request("request_id", "request_sn", [
                      req_param1, req_param2, req_param3, req_param4])

        id_lookup = {req.id: req}
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[],
                              negative_responses=[])
        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service],
                               requests=[req],
                               id_lookup=id_lookup)
        self.assertDictEqual(diag_layer._build_coded_prefix_tree(), {
                             0x12: {0x34: {0x56: {0x78: {-1: [service]}}}}})

        coded_message = bytes([0x12, 0x34, 0x56, 0x78])
        expected_message = Message(coded_message, service, req, param_dict={"SID": 0x12,
                                                                            "coded_const_parameter_2": 0x56,
                                                                            "coded_const_parameter_3": 0x34,
                                                                            "coded_const_parameter_4": 0x78})
        decoded_message = diag_layer.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message,
                         decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.structure, decoded_message.structure)
        self.assertEqual(expected_message.param_dict,
                         decoded_message.param_dict)

    def test_decode_request_structure(self):
        """Test the decoding for a structure."""
        id_lookup = {}
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        diag_coded_type_4 = StandardLengthType("A_UINT32", 4)

        compu_method = IdenticalCompuMethod("A_INT32", "A_INT32")
        dop = DataObjectProperty("dop.id",
                                 "dop_sn",
                                 diag_coded_type_4,
                                 physical_data_type="A_UINT32",
                                 compu_method=compu_method)
        id_lookup.update({dop.id: dop})

        req_param1 = CodedConstParameter("SID",
                                         diag_coded_type,
                                         coded_value=0x12,
                                         byte_position=0)

        struct_param1 = CodedConstParameter(
            "struct_param_1", diag_coded_type_4, coded_value=0x4, byte_position=0, bit_position=0)
        struct_param2 = ValueParameter(
            "struct_param_2", dop=dop, byte_position=0, bit_position=4)
        struct = Structure("struct_id", "struct", [
                           struct_param1, struct_param2])
        id_lookup.update({struct.id: struct})
        req_param2 = ValueParameter("structured_param", dop=struct)

        req = Request("request_id", "request_sn", [
                      req_param1, req_param2])
        id_lookup.update({req.id: req})
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[],
                              negative_responses=[])
        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service],
                               requests=[req],
                               id_lookup=id_lookup)

        coded_message = bytes([0x12, 0x34])
        expected_message = Message(coded_message, service, req,
                                   param_dict={"SID": 0x12,
                                               "structured_param": {"struct_param_1": 4, "struct_param_2": 3}})
        decoded_message = diag_layer.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message,
                         decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.structure, decoded_message.structure)
        self.assertEqual(expected_message.param_dict,
                         decoded_message.param_dict)

    def test_decode_request_end_of_pdu_field(self):
        """Test the decoding for a structure."""
        id_lookup = {}
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        diag_coded_type_4 = StandardLengthType("A_UINT32", 4)

        compu_method = IdenticalCompuMethod("A_INT32", "A_INT32")
        dop = DataObjectProperty("dop.id",
                                 "dop_sn",
                                 diag_coded_type_4,
                                 physical_data_type="A_UINT32",
                                 compu_method=compu_method)
        id_lookup.update({dop.id: dop})

        req_param1 = CodedConstParameter("SID",
                                         diag_coded_type,
                                         coded_value=0x12,
                                         byte_position=0)

        struct_param1 = CodedConstParameter(
            "struct_param_1", diag_coded_type_4, coded_value=0x4, byte_position=0, bit_position=0)
        struct_param2 = ValueParameter(
            "struct_param_2", dop=dop, byte_position=0, bit_position=4)
        struct = Structure("struct_id", "struct", [
                           struct_param1, struct_param2])
        id_lookup.update({struct.id: struct})
        eopf = EndOfPduField("eopf_id", "eopf_sn",
                             structure=struct,
                             is_visible=True)
        id_lookup.update({eopf.id: eopf})

        req_param2 = ValueParameter("eopf_param", dop=eopf)

        req = Request("request_id", "request_sn", [
                      req_param1, req_param2])
        id_lookup.update({req.id: req})
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[],
                              negative_responses=[])
        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service],
                               requests=[req],
                               id_lookup=id_lookup)

        coded_message = bytes([0x12, 0x34, 0x34])
        expected_message = Message(coded_message, service, req,
                                   param_dict={"SID": 0x12,
                                               "eopf_param": [{"struct_param_1": 4, "struct_param_2": 3},
                                                              {"struct_param_1": 4, "struct_param_2": 3}]})
        decoded_message = diag_layer.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message,
                         decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.structure, decoded_message.structure)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_decode_request_linear_compu_method(self):
        id_lookup = {}

        compu_method = LinearCompuMethod(1, 5, "A_INT32", "A_INT32")
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        dop = DataObjectProperty("linear.dop.id",
                                 "linear.dop.sn",
                                 diag_coded_type,
                                 physical_data_type="A_UINT32",
                                 compu_method=compu_method)
        id_lookup[dop.id] = dop
        req_param1 = CodedConstParameter("SID",
                                         diag_coded_type,
                                         coded_value=0x7d,
                                         byte_position=0)
        req_param2 = ValueParameter("value_parameter_2",
                                    dop=dop,
                                    byte_position=1)
        req = Request("request_id", "request_sn", [req_param1, req_param2])

        id_lookup[req.id] = req
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[],
                              negative_responses=[])
        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service],
                               requests=[req],
                               positive_responses=[],
                               id_lookup=id_lookup)

        coded_message = bytes([0x7d, 0x12])
        # The physical value of the second parameter is decode(0x12) = decode(18) = 5 * 18 + 1 = 91
        expected_message = Message(coded_message,
                                   service,
                                   req,
                                   param_dict={"SID": 0x7d,
                                               "value_parameter_2": 91})
        decoded_message = diag_layer.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message,
                         decoded_message.coded_message)
        self.assertEqual(expected_message.service,
                         decoded_message.service)
        self.assertEqual(expected_message.structure,
                         decoded_message.structure)
        self.assertEqual(expected_message.param_dict,
                         decoded_message.param_dict)

    def test_decode_response(self):
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        req_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x12, byte_position=0)
        req_param2 = CodedConstParameter(
            "req_param", diag_coded_type, coded_value=0xab, byte_position=1)
        req = Request("request_id", "request_sn", [req_param1, req_param2])

        resp_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x34, byte_position=0)
        resp_param2 = MatchingRequestParameter(
            "matching_req_param", request_byte_position=1, byte_length=1)
        pos_response = Response("pos_response_id", "pos_response_sn", [
                                resp_param1, resp_param2])

        resp_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x56, byte_position=0)
        resp_param2 = MatchingRequestParameter(
            "matching_req_param", request_byte_position=1, byte_length=1)
        neg_response = Response("neg_response_id", "neg_response_sn", [
                                resp_param1, resp_param2])

        id_lookup = {req.id: req, pos_response.id: pos_response,
                     neg_response.id: neg_response}
        service = DiagService(id="service_id",
                              short_name="service_sn",
                              request=req.id,
                              positive_responses=[pos_response.id],
                              negative_responses=[neg_response.id])
        diag_layer = DiagLayer("BASE-VARIANT",
                               id="dl_id",
                               short_name="dl_sn",
                               services=[service],
                               requests=[req],
                               positive_responses=[pos_response],
                               negative_responses=[neg_response],
                               id_lookup=id_lookup)

        for sid, message in [(0x34, pos_response), (0x56, neg_response)]:
            coded_message = bytes([sid, 0xab])
            expected_message = Message(coded_message, service, message,
                                       param_dict={"SID": sid, "matching_req_param": bytes([0xab])})
            decoded_message = diag_layer.decode(coded_message)[0]
            self.assertEqual(expected_message.coded_message,
                             decoded_message.coded_message)
            self.assertEqual(expected_message.service, decoded_message.service)
            self.assertEqual(expected_message.structure,
                             decoded_message.structure)
            self.assertEqual(expected_message.param_dict,
                             decoded_message.param_dict)

    def test_decode_dtc(self):
        id_lookup = {}
        diag_coded_type = StandardLengthType("A_UINT32", 8)
        compu_method = IdenticalCompuMethod("A_INT32", "A_INT32")

        dtc1 = DiagnosticTroubleCode("dtcID1",
                                     "P34_sn",
                                     0x34,
                                     "Error encountered",
                                     display_trouble_code="P34")
        dtc2 = DiagnosticTroubleCode("dtcID2",
                                     "P56_sn",
                                     0x56,
                                     "Crashed into wall",
                                     display_trouble_code="P56")
        dtcs = [dtc1, dtc2]
        dop = DtcDop("dtc.dop.id",
                     "dtc_dop_sn",
                     diag_coded_type,
                     physical_data_type="A_UINT32",
                     compu_method=compu_method,
                     dtcs=dtcs,
                     is_visible=True)
        id_lookup[dop.id] = dop
        resp_param1 = CodedConstParameter(
            "SID", diag_coded_type, coded_value=0x12, byte_position=0)
        resp_param2 = ValueParameter(
            "DTC_Param", dop=dop, byte_position=1)
        pos_response = Response("pos_response_id", "pos_response_sn",
                                [resp_param1, resp_param2])

        coded_message = bytes([0x12, 0x34])
        decoded_param_dict = pos_response.decode(coded_message)
        self.assertEqual(decoded_param_dict["DTC_Param"],
                         dtc1)


if __name__ == '__main__':
    unittest.main()
