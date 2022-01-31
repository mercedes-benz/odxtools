# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest

from odxtools.load_pdx_file import load_pdx_file

odxdb = load_pdx_file("./examples/somersault.pdx", enable_candela_workarounds=False)

class TestDecode(unittest.TestCase):

    def test_decode_request(self):
        messages = odxdb.ecus.somersault_assiduous.decode(bytes([0x03, 0x45]))
        self.assertTrue(len(messages) == 1)
        m = messages[0]
        self.assertEqual(m.coded_message, bytes([0x03, 0x45]))
        self.assertEqual(m.service, odxdb.ecus.somersault_assiduous.services.headstand)
        self.assertEqual(m.structure, odxdb.ecus.somersault_assiduous.services.headstand.request)
        self.assertEqual(m.param_dict, {"sid": 0x03, "duration": 0x45})
        
    def test_decode_inherited_request(self):
        raw_message = odxdb.ecus.somersault_assiduous.services.do_backward_flips(backward_soberness_check=0x21,
                                                                                 num_flips=2)
        messages = odxdb.ecus.somersault_assiduous.decode(raw_message)
        self.assertTrue(len(messages) == 1)
        m = messages[0]
        self.assertEqual(m.coded_message, bytes([0xbb, 0x21, 0x02]))
        self.assertEqual(m.service, odxdb.ecus.somersault_assiduous.services.do_backward_flips)
        self.assertEqual(m.structure, odxdb.ecus.somersault_assiduous.services.do_backward_flips.request)
        self.assertEqual(m.param_dict, {"sid": 0xbb, "backward_soberness_check": 0x21, "num_flips": 0x02})

    def test_decode_response(self):
        raw_request_message = odxdb.ecus.somersault_lazy.services.do_forward_flips(forward_soberness_check=0x12, num_flips=3)
        # TODO: responses currently don't seem to be inherited. (if
        # done, change "diag_layers.somersault" to
        # "ecus.somersault_lazy" here)
        db_response = next(filter(lambda x: x.short_name == "grudging_forward", odxdb.diag_layers.somersault.positive_responses))
        raw_response_message = db_response.encode(raw_request_message)
        
        messages = odxdb.diag_layers.somersault.decode_response(raw_response_message, raw_request_message)
        self.assertTrue(len(messages) == 1, f"There should be only one service for 0x0145 but there are: {messages}")
        m = messages[0]
        self.assertEqual(m.coded_message, bytes([0xfa, 0x03]))
        self.assertEqual(m.structure, db_response)
        self.assertEqual(m.param_dict,
                         { 'sid': 0xfa, 'num_flips_done': bytearray([0x03]) })


class TestNavigation(unittest.TestCase):

    def test_finding_services(self):
        # Find base variant
        self.assertIsNotNone(odxdb.diag_layers.somersault.services.do_backward_flips)
        self.assertIsNotNone(odxdb.diag_layers.somersault.services.do_forward_flips)
        self.assertIsNotNone(odxdb.diag_layers.somersault.services.report_status)

        # Find ecu variant
        self.assertIsNotNone(odxdb.ecus.somersault_assiduous.services.headstand)
        # Inherited services
        self.assertIsNotNone(odxdb.ecus.somersault_assiduous.services.do_backward_flips)
        self.assertIsNotNone(odxdb.ecus.somersault_assiduous.services.do_forward_flips)
        self.assertIsNotNone(odxdb.ecus.somersault_assiduous.services.report_status)
        self.assertIsNotNone(odxdb.ecus.somersault_assiduous.services.compulsory_program)

        # The lazy ECU variant only inherits services but does not add any.
        self.assertIsNotNone(odxdb.ecus.somersault_lazy.services.do_forward_flips)
        self.assertIsNotNone(odxdb.ecus.somersault_lazy.services.report_status)

        # also, the lazy ECU does not do backward flips. (this is
        # reserved for swots...)
        with self.assertRaises(AttributeError):
            odxdb.ecus.somersault_lazy.services.do_backward_flips

if __name__ == '__main__':
    unittest.main()
