# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest

import odxtools.uds as uds
from odxtools.compumethods import IdenticalCompuMethod, LinearCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.decodestate import ParameterValuePair
from odxtools.diagcodedtypes import *
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayer import DiagLayer
from odxtools.diaglayertype import DIAG_LAYER_TYPE
from odxtools.odxlink import OdxDocFragment, OdxLinkId, OdxLinkRef
from odxtools.parameters import (CodedConstParameter, LengthKeyParameter,
                                 ValueParameter)
from odxtools.physicaltype import PhysicalType
from odxtools.structures import Request

doc_frags = [ OdxDocFragment("UnitTest", "WinneThePoh") ]

class TestLeadingLengthInfoType(unittest.TestCase):
    def test_decode_leading_length_info_type_bytefield(self):
        dct = LeadingLengthInfoType(base_data_type="A_BYTEFIELD", bit_length=6)
        state = DecodeState(bytes([0x2, 0x34, 0x56]), [], 0)
        internal, next_byte = dct.convert_bytes_to_internal(state, 0)
        self.assertEqual(internal, bytes([0x34, 0x56]))

        dct = LeadingLengthInfoType(base_data_type="A_BYTEFIELD", bit_length=5)
        state = DecodeState(bytes([0x1, 0xC2, 0x3, 0x4]), [], 1)
        # 0xC2 = 11000010, with bit_position=1 and bit_lenth=5, the extracted bits are 00001,
        # i.e. the leading length is 1, i.e. only the byte 0x3 should be extracted.
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=1)
        self.assertEqual(internal, bytes([0x3]))

    def test_decode_leading_length_info_type_zero_length(self):
        dct = LeadingLengthInfoType(base_data_type="A_BYTEFIELD", bit_length=8)
        state = DecodeState(bytes([0x0, 0x1]), [], 0)
        internal, next_byte = dct.convert_bytes_to_internal(state, 0)
        self.assertEqual(internal, bytes())
        self.assertEqual(next_byte, 1)

    def test_encode_leading_length_info_type_bytefield(self):
        dct = LeadingLengthInfoType(base_data_type="A_UTF8STRING", bit_length=6)
        state = EncodeState(bytes([]), {})
        byte_val = dct.convert_internal_to_bytes("4V", state, bit_position=1)
        self.assertEqual(byte_val, bytes([0x4, 0x34, 0x56]))

        dct = LeadingLengthInfoType(base_data_type="A_BYTEFIELD", bit_length=5)
        state = EncodeState(bytes([]), {})
        internal = dct.convert_internal_to_bytes(bytes([0x3]),
                                                 state,
                                                 bit_position=1)
        self.assertEqual(internal, bytes([0x2, 0x3]))

    def test_decode_leading_length_info_type_bytefield2(self):
        dct = LeadingLengthInfoType(base_data_type="A_BYTEFIELD", bit_length=8)
        state = EncodeState(bytes([0x12, 0x34]), {})
        byte_val = dct.convert_internal_to_bytes(
            bytes([0x0]), state, bit_position=0)
        # Right now `bytes([0x1, 0x0])` is the encoded value.
        # However, since bytes() is shorter and would be decoded
        # to the same value this may be changed...
        self.assertIn(byte_val, [bytes(), bytes([0x1, 0x0])])

    def test_decode_leading_length_info_type_unicode2string(self):
        dct = LeadingLengthInfoType(base_data_type="A_UNICODE2STRING",
                                    bit_length=8)
        state = DecodeState(bytes([0x12, 0x4, 0x00, 0x61, 0x00, 0x39]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=0)
        self.assertEqual(internal, "a9")
        self.assertEqual(next_byte, 6)

        dct = LeadingLengthInfoType(base_data_type="A_UNICODE2STRING",
                                    bit_length=8,
                                    is_highlow_byte_order_raw=False)
        state = DecodeState(bytes([0x12, 0x4, 0x61, 0x00, 0x39, 0x00]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=0)
        self.assertEqual(internal, "a9")
        self.assertEqual(next_byte, 6)

    def test_encode_leading_length_info_type_unicode2string(self):
        dct = LeadingLengthInfoType(base_data_type="A_UNICODE2STRING",
                                    bit_length=8)
        state = EncodeState(coded_message=bytes([0x12]), parameter_values={})
        byte_val = dct.convert_internal_to_bytes("a9",
                                                 state,
                                                 bit_position=0)
        self.assertEqual(byte_val, bytes([0x4, 0x00, 0x61, 0x00, 0x39]))

        dct = LeadingLengthInfoType(base_data_type="A_UNICODE2STRING",
                                    bit_length=8,
                                    is_highlow_byte_order_raw=False)
        byte_val = dct.convert_internal_to_bytes("a9",
                                                 state,
                                                 bit_position=0)
        self.assertEqual(byte_val, bytes([0x4, 0x61, 0x00, 0x39, 0x00]))

    def test_end_to_end(self):
        # diag coded types
        diagcodedtypes = {
            "uint8":
            StandardLengthType(
                base_data_type="A_UINT32",
                bit_length=8),

            "certificateClient":
            LeadingLengthInfoType(base_data_type="A_BYTEFIELD", bit_length=8)
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
            IdenticalCompuMethod(
                internal_type="A_UINT32",
                physical_type="A_UINT32"),

            "bytes_passthrough":
            IdenticalCompuMethod(
                internal_type="A_BYTEFIELD",
                physical_type="A_BYTEFIELD"),
        }

        # data object properties
        dops = {
            "certificateClient":
            DataObjectProperty(
                odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                short_name="certificateClient",
                diag_coded_type=diagcodedtypes["certificateClient"],
                physical_type=PhysicalType("A_BYTEFIELD"),
                compu_method=compumethods["bytes_passthrough"]),
        }

        # Request
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            parameters=[
                CodedConstParameter(
                    short_name="SID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.SID.Authentication.value,
                    semantic="SERVICE-ID"
                ),
                ValueParameter(
                    short_name="certificateClient",
                    description=("The certificate to verify."),
                    byte_position=1,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id)
                ),
            ]
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        diag_layer = DiagLayer(
            variant_type=DIAG_LAYER_TYPE.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            requests=[request],
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=dops.values())
        )
        diag_layer.finalize_init()

        # Test decoding.
        coded_request = bytes([0x29,  # SID for Authentication
                               0x03,  # Byte length of the certificate
                               0x12,  # A very short
                               0x34,  # certificate
                               0x56,  # of three bytes
                               ])
        self.assertEqual(request.decode(coded_request), {
                         'SID': 0x29, 'certificateClient': bytes([0x12, 0x34, 0x56])})

        # Test encoding.
        self.assertEqual(request.encode(
            certificateClient=0x123456.to_bytes(3, 'big')), 0x2903123456.to_bytes(5, 'big'))


class TestStandardLengthType(unittest.TestCase):
    def test_decode_standard_length_type_uint(self):
        dct = StandardLengthType(base_data_type="A_UINT32", bit_length=5)
        state = DecodeState(bytes([0x1, 0x72, 0x3]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=1)
        self.assertEqual(internal, 25)
        self.assertEqual(next_byte, 2)

    def test_decode_standard_length_type_uint_byteorder(self):
        dct = StandardLengthType(base_data_type="A_UINT32", bit_length=16, is_highlow_byte_order_raw=False)
        state = DecodeState(bytes([0x1, 0x2, 0x3]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=0)
        self.assertEqual(internal, 0x0302)
        self.assertEqual(next_byte, 3)

    def test_decode_standard_length_type_bytes(self):
        dct = StandardLengthType(base_data_type="A_BYTEFIELD", bit_length=16)
        state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=0)
        self.assertEqual(internal, bytes([0x34, 0x56]))
        self.assertEqual(next_byte, 3)


class TestParamLengthInfoType(unittest.TestCase):
    def test_decode_param_info_length_type_uint(self):
        length_key_id = OdxLinkId("param.length_key", doc_frags)
        dct = ParamLengthInfoType(base_data_type="A_UINT32",
                                  length_key_id=length_key_id)
        state = DecodeState(bytes([0x10, 0x12, 0x34, 0x56]),
                            [ParameterValuePair(
                                parameter=LengthKeyParameter(short_name="length_key",
                                                             odx_id=length_key_id,
                                                             dop_ref=OdxLinkRef("some_dop", doc_frags)),
                                value=16
                            )],
                            next_byte_position=1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=0)
        self.assertEqual(internal, 0x1234)
        self.assertEqual(next_byte, 3)

    def test_encode_param_info_length_type_uint(self):
        length_key_id = OdxLinkId("param.length_key", doc_frags)
        dct = ParamLengthInfoType(base_data_type="A_UINT32",
                                  length_key_id=length_key_id)
        state = EncodeState(bytes([0x10]), {}, length_keys={length_key_id: 40})
        byte_val = dct.convert_internal_to_bytes(0x12345,
                                                 state,
                                                 bit_position=0)
        self.assertEqual(byte_val, bytes([0x0, 0x0, 0x1, 0x23, 0x45]))

    def test_end_to_end(self):
        # diag coded types
        diagcodedtypes = {
            "uint8":
            StandardLengthType(
                base_data_type="A_UINT32",
                bit_length=8),

            "length_key_id_to_lengthOfCertificateClient":
            ParamLengthInfoType(base_data_type="A_UINT32",
                                length_key_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate.lengthOfCertificateClient", doc_frags))
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
            IdenticalCompuMethod(
                internal_type="A_UINT32",
                physical_type="A_UINT32"),

            "multiply_with_8":
            LinearCompuMethod(
                offset=0,
                factor=8,
                internal_type="A_UINT32",
                physical_type="A_UINT32",
            ),
        }

        # data object properties
        dops = {
            "uint8_times_8":
            DataObjectProperty(
                odx_id=OdxLinkId("BV.dummy_DL.DOP.uint8_times_8", doc_frags),
                short_name="uint8_times_8",
                diag_coded_type=diagcodedtypes["uint8"],
                physical_type=PhysicalType("A_UINT32"),
                compu_method=compumethods["multiply_with_8"]),

            "certificateClient":
            DataObjectProperty(
                odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                short_name="certificateClient",
                diag_coded_type=diagcodedtypes["length_key_id_to_lengthOfCertificateClient"],
                physical_type=PhysicalType("A_UINT32"),
                compu_method=compumethods["uint_passthrough"]),
        }

        # Request using LengthKeyParameter and ParamLengthInfoType
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            parameters=[
                CodedConstParameter(
                    short_name="SID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.SID.Authentication.value,
                    semantic="SERVICE-ID"
                ),
                LengthKeyParameter(
                    short_name="lengthOfCertificateClient",
                    # LengthKeyParams have an ID to be referenced by a ParamLengthInfoType (which is a diag coded type)
                    odx_id=diagcodedtypes["length_key_id_to_lengthOfCertificateClient"].length_key_id,
                    description=("Length parameter for certificateClient."),
                    byte_position=1,
                    # The DOP multiplies the coded value by 8, since the length key ref expects the number of bits.
                    dop_ref=OdxLinkRef.from_id(dops["uint8_times_8"].odx_id)
                ),
                ValueParameter(
                    short_name="certificateClient",
                    description=("The certificate to verify."),
                    byte_position=2,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id)
                ),
            ]
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        diag_layer = DiagLayer(
            variant_type=DIAG_LAYER_TYPE.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            requests=[request],
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=dops.values())
        )
        diag_layer.finalize_init()

        # Test decoding.
        coded_request = bytes([0x29,  # SID for Authentication
                               0x03,  # Byte length of the certificate
                               0x12,  # A very short
                               0x34,  # certificate
                               0x56,  # of three bytes
                               ])

        self.assertEqual(request.decode(coded_request),
                         {'SID': 0x29,
                          'lengthOfCertificateClient': 24,
                          'certificateClient': 0x123456})

        self.assertEqual(request.encode(lengthOfCertificateClient=24,
                                        certificateClient=0x123456),
                         coded_request)

        # Automatic bit length calculation
        self.assertEqual(request.encode(certificateClient=0x123456),
                         coded_request)


class TestMinMaxLengthType(unittest.TestCase):
    def test_decode_min_max_length_type_bytes(self):
        dct = MinMaxLengthType(base_data_type="A_BYTEFIELD", min_length=1,
                               max_length=4, termination="HEX-FF")
        state = DecodeState(bytes([0x12, 0xFF, 0x34, 0x56, 0xFF]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state,
                                                            bit_position=0)
        self.assertEqual(internal, bytes([0xFF, 0x34, 0x56]))
        self.assertEqual(next_byte, 5)

    def test_decode_min_max_length_type_too_short_pdu(self):
        """If the PDU ends before min length is reached, an error must be raised."""
        dct = MinMaxLengthType(base_data_type="A_BYTEFIELD", min_length=2,
                               max_length=4, termination="HEX-FF")
        state = DecodeState(bytes([0x12, 0xFF]), [], 1)
        self.assertRaises(DecodeError, dct.convert_bytes_to_internal, state)

    def test_decode_min_max_length_type_end_of_pdu(self):
        """If the PDU ends before max length is reached, the extracted value ends at the end of the PDU."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(base_data_type="A_BYTEFIELD", min_length=2, max_length=5, termination=termination)
            state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78, 0x9A]), [], 1)
            internal, next_byte = dct.convert_bytes_to_internal(state,
                                                                bit_position=0)
            self.assertEqual(internal, bytes([0x34, 0x56, 0x78, 0x9A]))
            self.assertEqual(next_byte, 5)

    def test_decode_min_max_length_type_max_length(self):
        """If the max length is smaller than the end of PDU, the extracted value ends after max length."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(base_data_type="A_BYTEFIELD",
                                   min_length=2,
                                   max_length=3,
                                   termination=termination)
            state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78, 0x9A]), [], 1)
            internal, next_byte = dct.convert_bytes_to_internal(state,
                                                                bit_position=0)
            self.assertEqual(internal, bytes([0x34, 0x56, 0x78]))
            self.assertEqual(next_byte, 4)

    def test_encode_min_max_length_type_hex_ff(self):
        dct = MinMaxLengthType(base_data_type="A_BYTEFIELD", min_length=1,
                               max_length=4, termination="HEX-FF")
        state = EncodeState(bytes([0x12]),
                            parameter_values={},
                            is_end_of_pdu=False)
        byte_val = dct.convert_internal_to_bytes(bytes([0x34, 0x56]),
                                                 state,
                                                 bit_position=0)
        self.assertEqual(byte_val, bytes([0x34, 0x56, 0xFF]))

    def test_encode_min_max_length_type_zero(self):
        dct = MinMaxLengthType(base_data_type="A_UTF8STRING", min_length=2,
                               max_length=4, termination="ZERO")
        state = EncodeState(bytes([0x12]),
                            parameter_values={},
                            is_end_of_pdu=False)
        byte_val = dct.convert_internal_to_bytes("Hi",
                                                 state,
                                                 bit_position=0)
        self.assertEqual(byte_val, bytes([0x48, 0x69, 0x0]))

    def test_encode_min_max_length_type_end_of_pdu(self):
        """If the parameter is at the end of the PDU, no termination char is added."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(base_data_type="A_BYTEFIELD",
                                   min_length=2,
                                   max_length=5,
                                   termination=termination)
            state = EncodeState(bytes([0x12]),
                                parameter_values={},
                                is_end_of_pdu=True)
            byte_val = dct.convert_internal_to_bytes(bytes([0x34, 0x56, 0x78, 0x9A]),
                                                     state,
                                                     bit_position=0)
            self.assertEqual(byte_val, bytes([0x34, 0x56, 0x78, 0x9A]))

        dct = MinMaxLengthType(base_data_type="A_BYTEFIELD",
                               min_length=2,
                               max_length=5,
                               termination="END-OF-PDU")
        state = EncodeState(bytes([0x12]),
                            parameter_values={},
                            is_end_of_pdu=False)

    def test_encode_min_max_length_type_max_length(self):
        """If the internal value is larger than max length, an EncodeError must be raised."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(base_data_type="A_BYTEFIELD",
                                   min_length=2,
                                   max_length=3,
                                   termination=termination)
            state = EncodeState(bytes([0x12]),
                                parameter_values={},
                                is_end_of_pdu=True)
            byte_val = dct.convert_internal_to_bytes(bytes([0x34, 0x56, 0x78]),
                                                     state,
                                                     bit_position=0)
            self.assertEqual(byte_val, bytes([0x34, 0x56, 0x78]))
            self.assertRaises(EncodeError,
                              dct.convert_internal_to_bytes,
                              bytes([0x34, 0x56, 0x78, 0x9A]),
                              state,
                              bit_position=0)

    def test_end_to_end(self):
        # diag coded types
        diagcodedtypes = {
            "uint8":
            StandardLengthType(
                base_data_type="A_UINT32",
                bit_length=8),

            "certificateClient":
            MinMaxLengthType(base_data_type="A_BYTEFIELD",
                             min_length=2, max_length=10, termination="ZERO")
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
            IdenticalCompuMethod(
                internal_type="A_UINT32",
                physical_type="A_UINT32"),

            "bytes_passthrough":
            IdenticalCompuMethod(
                internal_type="A_BYTEFIELD",
                physical_type="A_BYTEFIELD"),
        }

        # data object properties
        dops = {
            "certificateClient":
            DataObjectProperty(
                odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                short_name="certificateClient",
                diag_coded_type=diagcodedtypes["certificateClient"],
                physical_type=PhysicalType("A_BYTEFIELD"),
                compu_method=compumethods["bytes_passthrough"]),
        }

        # Request
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            parameters=[
                CodedConstParameter(
                    short_name="SID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.SID.Authentication.value,
                    semantic="SERVICE-ID"
                ),
                ValueParameter(
                    short_name="certificateClient",
                    description=("The certificate to verify."),
                    byte_position=1,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id)
                ),
                CodedConstParameter(
                    short_name="dummy",
                    diag_coded_type=diagcodedtypes["uint8"],
                    coded_value=0x99
                ),
            ]
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        diag_layer = DiagLayer(
            variant_type=DIAG_LAYER_TYPE.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            requests=[request],
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=dops.values())
        )
        diag_layer.finalize_init()

        # Test decoding.
        coded_request = bytes([0x29,  # SID for Authentication
                               0x12,  # A very short
                               0x34,  # certificate
                               0x56,  # of three bytes
                               0x00,  # end of min-max length
                               0x99
                               ])
        self.assertEqual(request.decode(coded_request),
                         {'SID': 0x29,
                          'certificateClient': bytes([0x12, 0x34, 0x56]),
                          'dummy': 0x99})

        # Test encoding.
        self.assertEqual(request.encode(certificateClient=0x123456.to_bytes(3, 'big')),
                         coded_request)


if __name__ == '__main__':
    unittest.main()
