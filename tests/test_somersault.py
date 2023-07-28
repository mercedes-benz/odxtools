# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import unittest

from odxtools.load_pdx_file import load_pdx_file
from odxtools.odxlink import OdxLinkRef

try:
    from unittest.mock import patch  # type: ignore
except ImportError:
    from mock import patch  # type: ignore

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

odxdb = load_pdx_file("./examples/somersault.pdx")


class TestDatabase(unittest.TestCase):

    def test_db_structure(self):
        self.assertEqual([x.short_name for x in odxdb.diag_layer_containers], ["somersault"])

        self.assertEqual(
            [x.short_name for x in odxdb.diag_layers],
            ["somersault", "somersault_lazy", "somersault_assiduous"],
        )

        self.assertEqual([x.short_name for x in odxdb.ecus],
                         ["somersault_lazy", "somersault_assiduous"])

    def test_admin_data(self):
        dlc = odxdb.diag_layer_containers.somersault

        self.assertTrue(dlc.admin_data is not None)
        ad = dlc.admin_data

        self.assertEqual(ad.language, "en-US")

        self.assertTrue(ad.company_doc_infos is not None)
        cdi = ad.company_doc_infos

        self.assertEqual(len(cdi), 1)
        self.assertEqual(cdi[0].company_data_ref.ref_id, "CD.Suncus")
        self.assertTrue(cdi[0].company_data is not None)
        self.assertEqual(cdi[0].team_member_ref.ref_id, "TM.Doggy")
        self.assertTrue(cdi[0].team_member is not None)
        self.assertEqual(cdi[0].doc_label, "A really meaningful label")

        self.assertTrue(ad.doc_revisions is not None)
        dr = ad.doc_revisions[0]

        self.assertEqual(len(dr.modifications), 2)
        mod = dr.modifications[0]

        self.assertEqual(mod.change, "add somersault ECU")
        self.assertEqual(mod.reason, "we needed a new artist")

        self.assertEqual(dr.revision_label, "1.0")
        self.assertEqual(dr.team_member_ref.ref_id, "TM.Doggy")
        self.assertTrue(dr.team_member is not None)
        self.assertEqual(dr.tool, "odxtools 0.0.1")

    def test_company_datas(self):
        dlc = odxdb.diag_layer_containers.somersault

        self.assertTrue(dlc.company_datas is not None)
        cds = dlc.company_datas

        self.assertEqual([x.short_name for x in cds], ["Suncus", "ACME_Corporation"])

        cd = cds.Suncus
        self.assertEqual(cd.odx_id.local_id, "CD.Suncus")
        self.assertEqual(cd.short_name, "Suncus")
        self.assertEqual(cd.long_name, "Circus of the sun")
        self.assertEqual(cd.description, "<p>Prestigious group of performers</p>")
        self.assertEqual(cd.roles, ["circus", "gym"])

        self.assertEqual([x.short_name for x in cd.team_members], ["Doggy", "Horsey"])

        doggy = cd.team_members.Doggy
        self.assertEqual(doggy.odx_id.local_id, "TM.Doggy")
        self.assertEqual(doggy.short_name, "Doggy")
        self.assertEqual(doggy.long_name, "Doggy the dog")
        self.assertEqual(doggy.description, "<p>Dog is man's best friend</p>")
        self.assertEqual(doggy.roles, ["gymnast", "tracker"])
        self.assertEqual(doggy.department, "sniffers")
        self.assertEqual(doggy.address, "Some road")
        self.assertEqual(doggy.zip, "12345")
        self.assertEqual(doggy.city, "New Dogsville")
        self.assertEqual(doggy.phone, "+0 1234/5678-9")
        self.assertEqual(doggy.fax, "+0 1234/5678-0")
        self.assertEqual(doggy.email, "info@suncus.com")

        self.assertTrue(cd.company_specific_info is not None)
        self.assertTrue(cd.company_specific_info.related_docs is not None)

        rd = cd.company_specific_info.related_docs[0]

        self.assertEqual(rd.description, "<p>We are the best!</p>")
        self.assertTrue(rd.xdoc is not None)

        xdoc = rd.xdoc
        self.assertEqual(xdoc.short_name, "best")
        self.assertEqual(xdoc.long_name, "suncus is the best")
        self.assertEqual(xdoc.description, "<p>great propaganda...</p>")
        self.assertEqual(xdoc.number, "1")
        self.assertEqual(xdoc.state, "published")
        self.assertEqual(xdoc.date, "2015-01-15T20:15:20+05:00")
        self.assertEqual(xdoc.publisher, "Suncus Publishing")
        self.assertEqual(xdoc.url, "https://suncus-is-the-best.com")
        self.assertEqual(xdoc.position, "first!")

    def test_somersault_lazy(self):
        # TODO: this test is far from exhaustive
        ecu = odxdb.ecus.somersault_lazy

        self.assertEqual(
            {x.short_name
             for x in ecu.diag_comms},
            {
                "compulsory_program",
                "do_forward_flips",
                "report_status",
                "session_start",
                "session_stop",
                "tester_present",
            },
        )

        service = ecu.services.do_forward_flips
        self.assertEqual(
            [x.short_name for x in service.request.parameters],
            ["sid", "forward_soberness_check", "num_flips"],
        )
        self.assertEqual(
            [x.short_name for x in service.request.required_parameters],
            ["forward_soberness_check", "num_flips"],
        )
        self.assertEqual(service.request.bit_length, 24)

        self.assertEqual([x.short_name for x in service.positive_responses], ["grudging_forward"])
        self.assertEqual([x.short_name for x in service.negative_responses], ["flips_not_done"])

        pr = service.positive_responses.grudging_forward
        self.assertEqual([x.short_name for x in pr.parameters], ["sid", "num_flips_done"])
        self.assertEqual([x.short_name for x in pr.required_parameters], ["num_flips_done"])
        self.assertEqual(pr.bit_length, 16)

        nr = service.negative_responses.flips_not_done
        self.assertEqual(
            [x.short_name for x in nr.parameters],
            ["sid", "rq_sid", "reason", "flips_successfully_done"],
        )
        self.assertEqual(nr.bit_length, 32)

        nrc_const = nr.parameters.reason
        self.assertEqual(nrc_const.parameter_type, "NRC-CONST")
        self.assertEqual(nrc_const.coded_values, [0, 1, 2])


class TestDecode(unittest.TestCase):

    def test_decode_request(self):
        messages = odxdb.ecus.somersault_assiduous.decode(bytes([0x03, 0x45]))
        self.assertTrue(len(messages) == 1)
        m = messages[0]
        self.assertEqual(m.coded_message, bytes([0x03, 0x45]))
        self.assertEqual(m.service, odxdb.ecus.somersault_assiduous.services.headstand)
        self.assertEqual(m.structure, odxdb.ecus.somersault_assiduous.services.headstand.request)
        self.assertEqual(m.param_dict, {"sid": 0x03, "duration": 0x45})

    def test_decode_global_negative_response(self):
        ecu = odxdb.ecus.somersault_assiduous
        coded_request = bytes([0x03, 0x45])

        self.assertEqual(len(ecu.global_negative_responses), 1)

        gnr = ecu.global_negative_responses.too_hot
        coded_response = gnr.encode(coded_request=coded_request, temperature=35)

        decoded = ecu.decode(coded_response)
        # the global negative response for the somersault ECUs does
        # not include any matching-request parameter, so decode()
        # returns one possible instance per service
        self.assertEqual(len(decoded), len(ecu.services))

        # if we specify the request, the result should become unique
        decoded = ecu.decode_response(coded_response, request=coded_request)
        self.assertEqual(len(decoded), 1)

        # make sure that the global negative response was decoded
        # correctly
        gnr = decoded[0]
        self.assertEqual(gnr.param_dict['temperature'], 35)

    def test_code_table_params(self):
        """en- and decode table parameters"""
        ecu = odxdb.ecus.somersault_assiduous
        pr = ecu.services.report_status.positive_responses.status_report

        # test the "no flips done yet" response
        resp_data = pr.encode(
            dizzyness_level=12,
            happiness_level=100,
            last_pos_response_key="none",  # <- name of the selected table row
            last_pos_response=("none", 123))
        self.assertEqual(resp_data.hex(), "620c64007b")

        decoded_resp_data = pr.decode(resp_data)
        self.assertEqual(decoded_resp_data["dizzyness_level"], 12)
        self.assertEqual(decoded_resp_data["happiness_level"], 100)
        self.assertEqual(decoded_resp_data["last_pos_response_key"], "none")
        self.assertEqual(decoded_resp_data["last_pos_response"][0], "none")
        self.assertEqual(decoded_resp_data["last_pos_response"][1], 123)

        # test the "forward flips grudgingly done" response. we define
        # the table key implicitly by the 'last_pos_response'
        # table-struct parameter this time
        resp_data = pr.encode(
            coded_request=bytearray([123] * 15),
            dizzyness_level=42,
            happiness_level=92,
            last_pos_response=("forward_grudging", {
                "dizzyness_level": 42
            }))
        self.assertEqual(resp_data.hex(), "622a5c03fa7b")

        decoded_resp_data = pr.decode(resp_data)
        self.assertEqual(decoded_resp_data["dizzyness_level"], 42)
        self.assertEqual(decoded_resp_data["happiness_level"], 92)
        self.assertEqual(decoded_resp_data["last_pos_response_key"], "forward_grudging")
        self.assertEqual(decoded_resp_data["last_pos_response"][0], "forward_grudging")
        self.assertEqual(
            set(decoded_resp_data["last_pos_response"][1].keys()), set(["sid", "num_flips_done"]))
        # the num_flips_done parameter is a matching request parameter
        # for this response, so it produces a binary blob. possibly,
        # it should be changed to a ValueParameter...
        self.assertEqual(decoded_resp_data["last_pos_response"][1]["num_flips_done"], bytes([123]))

        # test the "backward flips grudgingly done" response
        resp_data = pr.encode(
            dizzyness_level=75,
            happiness_level=3,
            last_pos_response=("backward_grudging", {
                'dizzyness_level': 75,
                'num_flips_done': 5,
                'grumpiness_level': 150
            }))
        self.assertEqual(resp_data.hex(), "624b030afb0596")

        decoded_resp_data = pr.decode(resp_data)
        self.assertEqual(decoded_resp_data["dizzyness_level"], 75)
        self.assertEqual(decoded_resp_data["happiness_level"], 3)
        self.assertEqual(decoded_resp_data["last_pos_response_key"], "backward_grudging")
        self.assertEqual(decoded_resp_data["last_pos_response"][0], "backward_grudging")
        self.assertEqual(
            set(decoded_resp_data["last_pos_response"][1].keys()),
            set(["sid", "num_flips_done", "grumpiness_level"]))
        self.assertTrue(isinstance(decoded_resp_data["last_pos_response"], tuple))
        self.assertEqual(len(decoded_resp_data["last_pos_response"]), 2)
        self.assertEqual(decoded_resp_data["last_pos_response"][0], "backward_grudging")
        self.assertEqual(decoded_resp_data["last_pos_response"][1]["num_flips_done"], 5)
        self.assertEqual(decoded_resp_data["last_pos_response"][1]["grumpiness_level"], 150)

    def test_decode_inherited_request(self):
        raw_message = odxdb.ecus.somersault_assiduous.services.do_backward_flips(
            backward_soberness_check=0x21, num_flips=2)
        messages = odxdb.ecus.somersault_assiduous.decode(raw_message)
        self.assertTrue(len(messages) == 1)
        m = messages[0]
        self.assertEqual(m.coded_message, bytes([0xBB, 0x21, 0x02]))
        self.assertEqual(m.service, odxdb.ecus.somersault_assiduous.services.do_backward_flips)
        self.assertEqual(m.structure,
                         odxdb.ecus.somersault_assiduous.services.do_backward_flips.request)
        self.assertEqual(m.param_dict, {
            "sid": 0xBB,
            "backward_soberness_check": 0x21,
            "num_flips": 0x02
        })

    def test_free_param_info(self):
        ecu = odxdb.ecus.somersault_lazy
        service = ecu.services.do_forward_flips
        request = service.request
        pos_response = service.positive_responses.grudging_forward
        neg_response = service.negative_responses.flips_not_done

        stdout = StringIO()
        with patch("sys.stdout", stdout):
            request.print_free_parameters_info()
            expected_output = "forward_soberness_check: uint8\nnum_flips: uint8\n"
            actual_output = stdout.getvalue()
            self.assertEqual(actual_output, expected_output)

        with patch("sys.stdout", stdout):
            pos_response.print_free_parameters_info()
            expected_output = "forward_soberness_check: uint8\nnum_flips: uint8\n"
            actual_output = stdout.getvalue()
            self.assertEqual(actual_output, expected_output)

        with patch("sys.stdout", stdout):
            neg_response.print_free_parameters_info()
            expected_output = (
                "forward_soberness_check: uint8\nnum_flips: uint8\nflips_successfully_done: uint8\n"
            )
            actual_output = stdout.getvalue()
            self.assertEqual(actual_output, expected_output)

    def test_decode_response(self):
        ecu = odxdb.ecus.somersault_lazy
        service = ecu.services.do_forward_flips
        raw_request_message = service(forward_soberness_check=0x12, num_flips=3)
        pos_response = service.positive_responses.grudging_forward

        raw_response_message = pos_response.encode(raw_request_message)

        messages = ecu.decode_response(raw_response_message, raw_request_message)
        self.assertTrue(
            len(messages) == 1,
            f"There should be only one service for 0x0145 but there are: {messages}",
        )
        m = messages[0]
        self.assertEqual(m.coded_message, bytes([0xFA, 0x03]))
        self.assertEqual(m.structure, pos_response)
        self.assertEqual(m.param_dict, {"sid": 0xFA, "num_flips_done": bytearray([0x03])})


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
        self.assertIsNotNone(odxdb.ecus.somersault_assiduous.single_ecu_jobs.compulsory_program)

        # The lazy ECU variant only inherits services but does not add any.
        self.assertIsNotNone(odxdb.ecus.somersault_lazy.services.do_forward_flips)
        self.assertIsNotNone(odxdb.ecus.somersault_lazy.services.report_status)

        # also, the lazy ECU does not do backward flips. (this is
        # reserved for swots...)
        with self.assertRaises(AttributeError):
            odxdb.ecus.somersault_lazy.services.do_backward_flips


if __name__ == "__main__":
    unittest.main()
