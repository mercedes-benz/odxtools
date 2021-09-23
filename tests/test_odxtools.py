# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import unittest

from odxtools.load_pdx_file import load_pdx_file

odxdb = load_pdx_file("./examples/somersault.pdx",
                      enable_candela_workarounds=False)


class TestDataObjectProperty(unittest.TestCase):

    def test_bit_length(self):
        self.dop = odxdb.id_lookup["somersault.DOP.num_flips"]
        self.assertEqual(self.dop.bit_length, 8)

    def test_convert_physical_to_internal(self):
        self.dop = odxdb.id_lookup["somersault.DOP.boolean"]
        self.assertEqual(self.dop.convert_physical_to_internal("false"), 0)
        self.assertEqual(self.dop.convert_physical_to_internal("true"), 1)


class TestComposeUDS(unittest.TestCase):

    def test_encode_with_coded_const(self):
        request = odxdb.id_lookup["somersault.RQ.tester_present"]
        self.assertEqual(bytes(request.encode()),
                         0x3e00.to_bytes(2, "big"))

    def test_encode_with_texttable(self):
        request = odxdb.id_lookup["somersault.RQ.set_operation_params"]
        self.assertEqual(bytes(request.encode(
            **{"use_fire_ring": "true"})), 0xbd01.to_bytes(2, "big"))
        self.assertEqual(bytes(request.encode(
            use_fire_ring = "false")), 0xbd00.to_bytes(2, "big"))

    def test_encode_response_with_matching_request_param_and_structure(self):
        request = odxdb.id_lookup["somersault.RQ.do_forward_flips"]
        response = odxdb.id_lookup["somersault.PR.happy_forward"]

        coded_request = request.encode(forward_soberness_check=0x12, num_flips=12)
        coded_response = response.encode(yeha_level=3, coded_request=coded_request)
        self.assertEqual(bytes(coded_response), 0xFA0003.to_bytes(3, "big"))


class TestNavigation(unittest.TestCase):

    def test_find_ecu_by_name(self):
        # TODO (?): Maybe a KeyError should be raised instead of
        # returning None if an ECU does not exist? (In this case, the
        # calling code usually cannot proceed meaingfully anyway.)
        ecu = odxdb.ecus["somersault_crazy"]
        self.assertEqual(ecu, None)

        ecu = odxdb.ecus["somersault_lazy"]
        self.assertEqual(ecu.id, "somersault_lazy")

    def test_find_service_by_name(self):
        ecu = odxdb.ecus["somersault_lazy"]

        service_names = [s.short_name for s in ecu.services]
        self.assertIn("session_start", service_names)
        self.assertIn("session_stop", service_names)
        self.assertIn("tester_present", service_names)
        self.assertIn("do_forward_flips", service_names)
        self.assertNotIn("do_backward_flips", service_names)
        self.assertIn("report_status", service_names)

        service = ecu.services.session_start
        self.assertEqual(service.id, "somersault.service.session_start")
        self.assertEqual(service.semantic, "SESSION")


if __name__ == '__main__':
    unittest.main()
