# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import unittest

from odxtools.load_pdx_file import load_pdx_file
from odxtools.odxlink import OdxDocFragment, OdxLinkRef

odxdb = load_pdx_file("./examples/somersault.pdx")

# use the diag layer container's document fragments as the default for
# resolving references
container_doc_frags = odxdb.diag_layer_containers.somersault.odx_id.doc_fragments


class TestDataObjectProperty(unittest.TestCase):

    def test_bit_length(self):
        self.dop = odxdb.odxlinks.resolve(
            OdxLinkRef("somersault.DOP.num_flips", container_doc_frags))
        self.assertEqual(self.dop.bit_length, 8)

    def test_convert_physical_to_internal(self):
        self.dop = odxdb.odxlinks.resolve(OdxLinkRef("somersault.DOP.boolean", container_doc_frags))
        self.assertEqual(self.dop.convert_physical_to_internal("false"), 0)
        self.assertEqual(self.dop.convert_physical_to_internal("true"), 1)


class TestComposeUDS(unittest.TestCase):

    def test_encode_with_coded_const(self):
        request = odxdb.odxlinks.resolve(
            OdxLinkRef("somersault.RQ.tester_present", container_doc_frags))
        self.assertEqual(bytes(request.encode()), 0x3E00.to_bytes(2, "big"))

    def test_encode_with_texttable(self):
        request = odxdb.odxlinks.resolve(
            OdxLinkRef("somersault.RQ.set_operation_params", container_doc_frags))
        self.assertEqual(
            bytes(request.encode(**{"use_fire_ring": "true"})), 0xBD01.to_bytes(2, "big"))
        self.assertEqual(bytes(request.encode(use_fire_ring="false")), 0xBD00.to_bytes(2, "big"))

    def test_encode_response_with_matching_request_param_and_structure(self):
        request = odxdb.odxlinks.resolve(
            OdxLinkRef("somersault.RQ.do_forward_flips", container_doc_frags))
        response = odxdb.odxlinks.resolve(
            OdxLinkRef("somersault.PR.happy_forward", container_doc_frags))

        coded_request = request.encode(forward_soberness_check=0x12, num_flips=12)
        coded_response = response.encode(yeha_level=3, coded_request=coded_request)
        self.assertEqual(bytes(coded_response), 0xFA0003.to_bytes(3, "big"))


class TestNavigation(unittest.TestCase):

    def test_find_ecu_by_name(self):
        with self.assertRaises(KeyError):
            ecu = odxdb.ecus["somersault_crazy"]
        with self.assertRaises(KeyError):
            ecu = odxdb.ecus[len(odxdb.ecus) + 10]

        ecu = odxdb.ecus.get("somersault_crazy")
        self.assertEqual(ecu, None)

        ecu = odxdb.ecus.get(len(odxdb.ecus) + 10)
        self.assertEqual(ecu, None)

        # make sure that NamedItemLists support slicing
        ecus = odxdb.ecus[-2:]
        self.assertEqual(len(ecus), 2)
        self.assertEqual(ecus[0].odx_id.local_id, "somersault_lazy")
        self.assertEqual(ecus[1].odx_id.local_id, "somersault_assiduous")

        ecu = odxdb.ecus["somersault_lazy"]
        self.assertEqual(ecu.odx_id.local_id, "somersault_lazy")

        ecu = odxdb.ecus[0]
        self.assertEqual(ecu.odx_id.local_id, "somersault_lazy")

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
        self.assertEqual(service.odx_id.local_id, "somersault.service.session_start")
        self.assertEqual(service.semantic, "SESSION")


if __name__ == "__main__":
    unittest.main()
