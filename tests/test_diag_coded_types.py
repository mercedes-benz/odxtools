# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import unittest
from xml.etree import ElementTree

import odxtools.uds as uds
from odxtools.compumethods import IdenticalCompuMethod, LinearCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import *
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayer import DiagLayer
from odxtools.diaglayerraw import DiagLayerRaw
from odxtools.diaglayertype import DiagLayerType
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.parameters import CodedConstParameter, LengthKeyParameter, ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.structures import Request
from odxtools.utils import short_name_as_id

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestLeadingLengthInfoType(unittest.TestCase):

    def test_decode_leading_length_info_type_bytefield(self):
        dct = LeadingLengthInfoType(
            base_data_type="A_BYTEFIELD",
            bit_length=6,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x2, 0x34, 0x56]), [], 0)
        internal, next_byte = dct.convert_bytes_to_internal(state, 0)
        self.assertEqual(internal, bytes([0x34, 0x56]))

        dct = LeadingLengthInfoType(
            base_data_type="A_BYTEFIELD",
            bit_length=5,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x1, 0xC2, 0x3, 0x4]), [], 1)
        # 0xC2 = 11000010, with bit_position=1 and bit_lenth=5, the extracted bits are 00001,
        # i.e. the leading length is 1, i.e. only the byte 0x3 should be extracted.
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=1)
        self.assertEqual(internal, bytes([0x3]))

    def test_decode_leading_length_info_type_zero_length(self):
        dct = LeadingLengthInfoType(
            base_data_type="A_BYTEFIELD",
            bit_length=8,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x0, 0x1]), [], 0)
        internal, next_byte = dct.convert_bytes_to_internal(state, 0)
        self.assertEqual(internal, bytes())
        self.assertEqual(next_byte, 1)

    def test_encode_leading_length_info_type_bytefield(self):
        dct = LeadingLengthInfoType(
            base_data_type="A_UTF8STRING",
            bit_length=6,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(bytes([]), {})
        byte_val = dct.convert_internal_to_bytes("4V", state, bit_position=1)
        self.assertEqual(byte_val, bytes([0x4, 0x34, 0x56]))

        dct = LeadingLengthInfoType(
            base_data_type="A_BYTEFIELD",
            bit_length=5,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(bytes([]), {})
        internal = dct.convert_internal_to_bytes(bytes([0x3]), state, bit_position=1)
        self.assertEqual(internal, bytes([0x2, 0x3]))

    def test_decode_leading_length_info_type_bytefield2(self):
        dct = LeadingLengthInfoType(
            base_data_type="A_BYTEFIELD",
            bit_length=8,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(bytes([0x12, 0x34]), {})
        byte_val = dct.convert_internal_to_bytes(bytes([0x0]), state, bit_position=0)
        # Right now `bytes([0x1, 0x0])` is the encoded value.
        # However, since bytes() is shorter and would be decoded
        # to the same value this may be changed...
        self.assertIn(byte_val, [bytes(), bytes([0x1, 0x0])])

    def test_decode_leading_length_info_type_unicode2string(self):
        dct = LeadingLengthInfoType(
            base_data_type="A_UNICODE2STRING",
            bit_length=8,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x12, 0x4, 0x00, 0x61, 0x00, 0x39]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
        self.assertEqual(internal, "a9")
        self.assertEqual(next_byte, 6)

        dct = LeadingLengthInfoType(
            base_data_type="A_UNICODE2STRING",
            bit_length=8,
            base_type_encoding=None,
            is_highlow_byte_order_raw=False,
        )
        state = DecodeState(bytes([0x12, 0x4, 0x61, 0x00, 0x39, 0x00]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
        self.assertEqual(internal, "a9")
        self.assertEqual(next_byte, 6)

    def test_encode_leading_length_info_type_unicode2string(self):
        dct = LeadingLengthInfoType(
            base_data_type="A_UNICODE2STRING",
            bit_length=8,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(coded_message=bytes([0x12]), parameter_values={})
        byte_val = dct.convert_internal_to_bytes("a9", state, bit_position=0)
        self.assertEqual(byte_val, bytes([0x4, 0x00, 0x61, 0x00, 0x39]))

        dct = LeadingLengthInfoType(
            base_data_type="A_UNICODE2STRING",
            bit_length=8,
            base_type_encoding=None,
            is_highlow_byte_order_raw=False,
        )
        byte_val = dct.convert_internal_to_bytes("a9", state, bit_position=0)
        self.assertEqual(byte_val, bytes([0x4, 0x61, 0x00, 0x39, 0x00]))

    def test_end_to_end(self):
        # diag coded types
        diagcodedtypes = {
            "uint8":
                StandardLengthType(
                    base_data_type="A_UINT32",
                    base_type_encoding=None,
                    bit_length=8,
                    bit_mask=None,
                    is_condensed_raw=None,
                    is_highlow_byte_order_raw=None,
                ),
            "certificateClient":
                LeadingLengthInfoType(
                    base_data_type="A_BYTEFIELD",
                    bit_length=8,
                    base_type_encoding=None,
                    is_highlow_byte_order_raw=None,
                ),
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
                IdenticalCompuMethod(internal_type="A_UINT32", physical_type="A_UINT32"),
            "bytes_passthrough":
                IdenticalCompuMethod(internal_type="A_BYTEFIELD", physical_type="A_BYTEFIELD"),
        }

        # data object properties
        dops = {
            "certificateClient":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                    short_name="certificateClient",
                    long_name=None,
                    description=None,
                    is_visible_raw=None,
                    diag_coded_type=diagcodedtypes["certificateClient"],
                    physical_type=PhysicalType("A_BYTEFIELD", display_radix=None, precision=None),
                    compu_method=compumethods["bytes_passthrough"],
                    unit_ref=None,
                    sdgs=[],
                ),
        }

        # Request
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="SID",
                    long_name=None,
                    description=None,
                    semantic="SERVICE-ID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    bit_position=None,
                    coded_value=uds.SID.Authentication.value,
                    sdgs=[],
                ),
                ValueParameter(
                    short_name="certificateClient",
                    long_name=None,
                    description="The certificate to verify.",
                    semantic=None,
                    byte_position=1,
                    bit_position=None,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    sdgs=[],
                ),
            ],
            byte_size=None,
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        diag_layer_raw = DiagLayerRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(short_name_as_id),
            functional_classes=NamedItemList(short_name_as_id),
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=dops.values(),
                dtc_dops=NamedItemList(short_name_as_id),
                structures=NamedItemList(short_name_as_id),
                end_of_pdu_fields=NamedItemList(short_name_as_id),
                tables=NamedItemList(short_name_as_id),
                env_data_descs=NamedItemList(short_name_as_id),
                env_datas=NamedItemList(short_name_as_id),
                muxs=NamedItemList(short_name_as_id),
                unit_spec=None,
                sdgs=[],
            ),
            diag_comms=[],
            requests=NamedItemList(short_name_as_id, [request]),
            positive_responses=NamedItemList(short_name_as_id),
            negative_responses=NamedItemList(short_name_as_id),
            global_negative_responses=NamedItemList(short_name_as_id),
            additional_audiences=NamedItemList(short_name_as_id),
            import_refs=[],
            state_charts=NamedItemList(short_name_as_id),
            sdgs=[],
            parent_refs=[],
            communication_parameters=[],
            ecu_variant_patterns=[],
        )
        diag_layer = DiagLayer(diag_layer_raw=diag_layer_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(diag_layer._build_odxlinks())
        diag_layer._resolve_odxlinks(odxlinks)
        diag_layer._finalize_init(odxlinks)

        # Test decoding.
        coded_request = bytes([
            0x29,  # SID for Authentication
            0x03,  # Byte length of the certificate
            0x12,  # A very short
            0x34,  # certificate
            0x56,  # of three bytes
        ])
        self.assertEqual(
            request.decode(coded_request),
            {
                "SID": 0x29,
                "certificateClient": bytes([0x12, 0x34, 0x56])
            },
        )

        # Test encoding.
        self.assertEqual(
            request.encode(certificateClient=0x123456.to_bytes(3, "big")),
            0x2903123456.to_bytes(5, "big"),
        )


class TestStandardLengthType(unittest.TestCase):

    def test_decode_standard_length_type_uint(self):
        dct = StandardLengthType(
            base_data_type="A_UINT32",
            base_type_encoding=None,
            bit_length=5,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x1, 0x72, 0x3]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=1)
        self.assertEqual(internal, 25)
        self.assertEqual(next_byte, 2)

    def test_decode_standard_length_type_uint_byteorder(self):
        dct = StandardLengthType(
            base_data_type="A_UINT32",
            base_type_encoding=None,
            bit_length=16,
            bit_mask=None,
            is_highlow_byte_order_raw=False,
            is_condensed_raw=None,
        )
        state = DecodeState(bytes([0x1, 0x2, 0x3]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
        self.assertEqual(internal, 0x0302)
        self.assertEqual(next_byte, 3)

    def test_decode_standard_length_type_bytes(self):
        dct = StandardLengthType(
            base_data_type="A_BYTEFIELD",
            base_type_encoding=None,
            bit_length=16,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
        self.assertEqual(internal, bytes([0x34, 0x56]))
        self.assertEqual(next_byte, 3)


class TestParamLengthInfoType(unittest.TestCase):

    def test_decode_param_info_length_type_uint(self):
        length_key_id = OdxLinkId("param.length_key", doc_frags)
        length_key_ref = OdxLinkRef.from_id(length_key_id)
        length_key = LengthKeyParameter(
            odx_id=length_key_id,
            short_name="length_key",
            long_name=None,
            description=None,
            semantic=None,
            sdgs=[],
            dop_ref=OdxLinkRef("DOP.uint8", doc_frags),
            dop_snref=None,
            byte_position=1,
            bit_position=None,
        )
        dct = ParamLengthInfoType(
            base_data_type="A_UINT32",
            base_type_encoding=None,
            length_key_ref=length_key_ref,
            is_highlow_byte_order_raw=None,
        )
        odxlinks = OdxLinkDatabase()
        odxlinks.update({length_key_id: length_key})
        dct._resolve_odxlinks(odxlinks)
        state = DecodeState(
            coded_message=bytes([0x10, 0x12, 0x34, 0x56]),
            parameter_values={length_key.short_name: 16},
            next_byte_position=1,
        )
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
        self.assertEqual(internal, 0x1234)
        self.assertEqual(next_byte, 3)

    def test_encode_param_info_length_type_uint(self):
        length_key_id = OdxLinkId("param.length_key", doc_frags)
        length_key = LengthKeyParameter(
            odx_id=length_key_id,
            short_name="length_key",
            long_name=None,
            description=None,
            semantic=None,
            sdgs=[],
            dop_ref=OdxLinkRef("DOP.uint8", doc_frags),
            dop_snref=None,
            byte_position=1,
            bit_position=None,
        )
        length_key_ref = OdxLinkRef.from_id(length_key_id)
        dct = ParamLengthInfoType(
            base_data_type="A_UINT32",
            base_type_encoding=None,
            length_key_ref=OdxLinkRef.from_id(length_key_id),
            is_highlow_byte_order_raw=None,
        )
        odxlinks = OdxLinkDatabase()
        odxlinks.update({length_key_id: length_key})
        dct._resolve_odxlinks(odxlinks)
        state = EncodeState(bytes([0x10]), {length_key.short_name: 40})
        byte_val = dct.convert_internal_to_bytes(0x12345, state, bit_position=0)
        self.assertEqual(byte_val.hex(), "0000012345")

    def test_end_to_end(self):
        # diag coded types
        diagcodedtypes = {
            "uint8":
                StandardLengthType(
                    base_data_type="A_UINT32",
                    base_type_encoding=None,
                    bit_length=8,
                    bit_mask=None,
                    is_condensed_raw=None,
                    is_highlow_byte_order_raw=None,
                ),
            "length_key_id_to_lengthOfCertificateClient":
                ParamLengthInfoType(
                    base_data_type="A_UINT32",
                    base_type_encoding=None,
                    length_key_ref=OdxLinkRef("param.dummy_length_key", doc_frags),
                    is_highlow_byte_order_raw=None,
                ),
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
                IdenticalCompuMethod(internal_type="A_UINT32", physical_type="A_UINT32"),
            "multiply_with_8":
                LinearCompuMethod(
                    offset=0,
                    factor=8,
                    denominator=1,
                    internal_type="A_UINT32",
                    physical_type="A_UINT32",
                    internal_lower_limit=None,
                    internal_upper_limit=None,
                ),
        }

        # data object properties
        dops = {
            "uint8_times_8":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.uint8_times_8", doc_frags),
                    short_name="uint8_times_8",
                    long_name=None,
                    description=None,
                    is_visible_raw=None,
                    diag_coded_type=diagcodedtypes["uint8"],
                    physical_type=PhysicalType("A_UINT32", display_radix=None, precision=None),
                    compu_method=compumethods["multiply_with_8"],
                    unit_ref=None,
                    sdgs=[],
                ),
            "certificateClient":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                    short_name="certificateClient",
                    long_name=None,
                    description=None,
                    is_visible_raw=None,
                    diag_coded_type=diagcodedtypes["length_key_id_to_lengthOfCertificateClient"],
                    physical_type=PhysicalType("A_UINT32", display_radix=None, precision=None),
                    compu_method=compumethods["uint_passthrough"],
                    unit_ref=None,
                    sdgs=[],
                ),
        }

        # Request using LengthKeyParameter and ParamLengthInfoType
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="SID",
                    long_name=None,
                    description=None,
                    semantic="SERVICE-ID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.SID.Authentication.value,
                    bit_position=None,
                    sdgs=[],
                ),
                LengthKeyParameter(
                    short_name="lengthOfCertificateClient",
                    long_name=None,
                    description="Length parameter for certificateClient.",
                    semantic=None,
                    # LengthKeyParams have an ID to be referenced by a ParamLengthInfoType (which is a diag coded type)
                    odx_id=OdxLinkId("param.dummy_length_key", doc_frags),
                    byte_position=1,
                    bit_position=None,
                    # The DOP multiplies the coded value by 8, since the length key ref expects the number of bits.
                    dop_ref=OdxLinkRef.from_id(dops["uint8_times_8"].odx_id),
                    dop_snref=None,
                    sdgs=[],
                ),
                ValueParameter(
                    short_name="certificateClient",
                    long_name=None,
                    description="The certificate to verify.",
                    semantic=None,
                    byte_position=2,
                    bit_position=None,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    sdgs=[],
                ),
            ],
            byte_size=None,
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        diag_layer_raw = DiagLayerRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(short_name_as_id),
            functional_classes=NamedItemList(short_name_as_id),
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=dops.values(),
                dtc_dops=NamedItemList(short_name_as_id),
                structures=NamedItemList(short_name_as_id),
                end_of_pdu_fields=NamedItemList(short_name_as_id),
                tables=NamedItemList(short_name_as_id),
                env_data_descs=NamedItemList(short_name_as_id),
                env_datas=NamedItemList(short_name_as_id),
                muxs=NamedItemList(short_name_as_id),
                unit_spec=None,
                sdgs=[],
            ),
            diag_comms=[],
            requests=NamedItemList(short_name_as_id, [request]),
            positive_responses=NamedItemList(short_name_as_id),
            negative_responses=NamedItemList(short_name_as_id),
            global_negative_responses=NamedItemList(short_name_as_id),
            additional_audiences=NamedItemList(short_name_as_id),
            import_refs=[],
            state_charts=NamedItemList(short_name_as_id),
            sdgs=[],
            parent_refs=[],
            communication_parameters=[],
            ecu_variant_patterns=[],
        )
        diag_layer = DiagLayer(diag_layer_raw=diag_layer_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(diag_layer._build_odxlinks())
        diag_layer._resolve_odxlinks(odxlinks)
        diag_layer._finalize_init(odxlinks)

        # Test decoding.
        coded_request = bytes([
            0x29,  # SID for Authentication
            0x03,  # Byte length of the certificate
            0x12,  # A very short
            0x34,  # certificate
            0x56,  # of three bytes
        ])

        self.assertEqual(
            request.decode(coded_request),
            {
                "SID": 0x29,
                "lengthOfCertificateClient": 24,
                "certificateClient": 0x123456
            },
        )

        self.assertEqual(
            request.encode(lengthOfCertificateClient=24, certificateClient=0x123456), coded_request)

        # Automatic bit length calculation
        self.assertEqual(request.encode(certificateClient=0x123456), coded_request)


class TestMinMaxLengthType(unittest.TestCase):

    def test_decode_min_max_length_type_bytes(self):
        dct = MinMaxLengthType(
            base_data_type="A_BYTEFIELD",
            base_type_encoding=None,
            min_length=1,
            max_length=4,
            termination="HEX-FF",
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x12, 0xFF, 0x34, 0x56, 0xFF]), [], 1)
        internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
        self.assertEqual(internal, bytes([0xFF, 0x34, 0x56]))
        self.assertEqual(next_byte, 5)

    def test_decode_min_max_length_type_too_short_pdu(self):
        """If the PDU ends before min length is reached, an error must be raised."""
        dct = MinMaxLengthType(
            base_data_type="A_BYTEFIELD",
            base_type_encoding=None,
            min_length=2,
            max_length=4,
            termination="HEX-FF",
            is_highlow_byte_order_raw=None,
        )
        state = DecodeState(bytes([0x12, 0xFF]), [], 1)
        self.assertRaises(DecodeError, dct.convert_bytes_to_internal, state)

    def test_decode_min_max_length_type_end_of_pdu(self):
        """If the PDU ends before max length is reached, the extracted value ends at the end of the PDU."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(
                base_data_type="A_BYTEFIELD",
                base_type_encoding=None,
                min_length=2,
                max_length=5,
                termination=termination,
                is_highlow_byte_order_raw=None,
            )
            state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78, 0x9A]), [], 1)
            internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
            self.assertEqual(internal, bytes([0x34, 0x56, 0x78, 0x9A]))
            self.assertEqual(next_byte, 5)

    def test_decode_min_max_length_type_max_length(self):
        """If the max length is smaller than the end of PDU, the extracted value ends after max length."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(
                base_data_type="A_BYTEFIELD",
                base_type_encoding=None,
                min_length=2,
                max_length=3,
                termination=termination,
                is_highlow_byte_order_raw=None,
            )
            state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78, 0x9A]), [], 1)
            internal, next_byte = dct.convert_bytes_to_internal(state, bit_position=0)
            self.assertEqual(internal, bytes([0x34, 0x56, 0x78]))
            self.assertEqual(next_byte, 4)

    def test_encode_min_max_length_type_hex_ff(self):
        dct = MinMaxLengthType(
            base_data_type="A_BYTEFIELD",
            base_type_encoding=None,
            min_length=1,
            max_length=4,
            termination="HEX-FF",
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(bytes([0x12]), parameter_values={}, is_end_of_pdu=False)
        byte_val = dct.convert_internal_to_bytes(bytes([0x34, 0x56]), state, bit_position=0)
        self.assertEqual(byte_val, bytes([0x34, 0x56, 0xFF]))

    def test_encode_min_max_length_type_zero(self):
        dct = MinMaxLengthType(
            base_data_type="A_UTF8STRING",
            base_type_encoding=None,
            min_length=2,
            max_length=4,
            termination="ZERO",
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(bytes([0x12]), parameter_values={}, is_end_of_pdu=False)
        byte_val = dct.convert_internal_to_bytes("Hi", state, bit_position=0)
        self.assertEqual(byte_val, bytes([0x48, 0x69, 0x0]))

    def test_encode_min_max_length_type_end_of_pdu(self):
        """If the parameter is at the end of the PDU, no termination char is added."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(
                base_data_type="A_BYTEFIELD",
                base_type_encoding=None,
                min_length=2,
                max_length=5,
                termination=termination,
                is_highlow_byte_order_raw=None,
            )
            state = EncodeState(bytes([0x12]), parameter_values={}, is_end_of_pdu=True)
            byte_val = dct.convert_internal_to_bytes(
                bytes([0x34, 0x56, 0x78, 0x9A]), state, bit_position=0)
            self.assertEqual(byte_val, bytes([0x34, 0x56, 0x78, 0x9A]))

        dct = MinMaxLengthType(
            base_data_type="A_BYTEFIELD",
            base_type_encoding=None,
            min_length=2,
            max_length=5,
            termination="END-OF-PDU",
            is_highlow_byte_order_raw=None,
        )
        state = EncodeState(bytes([0x12]), parameter_values={}, is_end_of_pdu=False)

    def test_encode_min_max_length_type_max_length(self):
        """If the internal value is larger than max length, an EncodeError must be raised."""
        for termination in ["END-OF-PDU", "HEX-FF", "ZERO"]:
            dct = MinMaxLengthType(
                base_data_type="A_BYTEFIELD",
                base_type_encoding=None,
                min_length=2,
                max_length=3,
                termination=termination,
                is_highlow_byte_order_raw=None,
            )
            state = EncodeState(bytes([0x12]), parameter_values={}, is_end_of_pdu=True)
            byte_val = dct.convert_internal_to_bytes(
                bytes([0x34, 0x56, 0x78]), state, bit_position=0)
            self.assertEqual(byte_val, bytes([0x34, 0x56, 0x78]))
            self.assertRaises(
                EncodeError,
                dct.convert_internal_to_bytes,
                bytes([0x34, 0x56, 0x78, 0x9A]),
                state,
                bit_position=0,
            )

    def test_end_to_end(self):
        # diag coded types
        diagcodedtypes = {
            "uint8":
                StandardLengthType(
                    base_data_type="A_UINT32",
                    base_type_encoding=None,
                    bit_length=8,
                    bit_mask=None,
                    is_condensed_raw=None,
                    is_highlow_byte_order_raw=None,
                ),
            "certificateClient":
                MinMaxLengthType(
                    base_data_type="A_BYTEFIELD",
                    base_type_encoding=None,
                    min_length=2,
                    max_length=10,
                    termination="ZERO",
                    is_highlow_byte_order_raw=None,
                ),
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
                IdenticalCompuMethod(internal_type="A_UINT32", physical_type="A_UINT32"),
            "bytes_passthrough":
                IdenticalCompuMethod(internal_type="A_BYTEFIELD", physical_type="A_BYTEFIELD"),
        }

        # data object properties
        dops = {
            "certificateClient":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                    short_name="certificateClient",
                    long_name=None,
                    description=None,
                    is_visible_raw=None,
                    diag_coded_type=diagcodedtypes["certificateClient"],
                    physical_type=PhysicalType("A_BYTEFIELD", display_radix=None, precision=None),
                    compu_method=compumethods["bytes_passthrough"],
                    unit_ref=None,
                    sdgs=[],
                ),
        }

        # Request
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="SID",
                    long_name=None,
                    description=None,
                    semantic="SERVICE-ID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.SID.Authentication.value,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    short_name="certificateClient",
                    long_name=None,
                    description=("The certificate to verify."),
                    semantic=None,
                    byte_position=1,
                    bit_position=None,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    short_name="dummy",
                    long_name=None,
                    description=None,
                    semantic=None,
                    diag_coded_type=diagcodedtypes["uint8"],
                    coded_value=0x99,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
            byte_size=None,
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        diag_layer_raw = DiagLayerRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(short_name_as_id),
            functional_classes=NamedItemList(short_name_as_id),
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=dops.values(),
                dtc_dops=NamedItemList(short_name_as_id),
                structures=NamedItemList(short_name_as_id),
                end_of_pdu_fields=NamedItemList(short_name_as_id),
                tables=NamedItemList(short_name_as_id),
                env_data_descs=NamedItemList(short_name_as_id),
                env_datas=NamedItemList(short_name_as_id),
                muxs=NamedItemList(short_name_as_id),
                unit_spec=None,
                sdgs=[],
            ),
            diag_comms=[],
            requests=NamedItemList(short_name_as_id, [request]),
            positive_responses=NamedItemList(short_name_as_id),
            negative_responses=NamedItemList(short_name_as_id),
            global_negative_responses=NamedItemList(short_name_as_id),
            additional_audiences=NamedItemList(short_name_as_id),
            import_refs=[],
            state_charts=NamedItemList(short_name_as_id),
            sdgs=[],
            parent_refs=[],
            communication_parameters=[],
            ecu_variant_patterns=[],
        )
        diag_layer = DiagLayer(diag_layer_raw=diag_layer_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(diag_layer._build_odxlinks())
        diag_layer._resolve_odxlinks(odxlinks)
        diag_layer._finalize_init(odxlinks)

        # Test decoding.
        coded_request = bytes([
            0x29,  # SID for Authentication
            0x12,  # A very short
            0x34,  # certificate
            0x56,  # of three bytes
            0x00,  # end of min-max length
            0x99,
        ])
        self.assertEqual(
            request.decode(coded_request),
            {
                "SID": 0x29,
                "certificateClient": bytes([0x12, 0x34, 0x56]),
                "dummy": 0x99
            },
        )

        # Test encoding.
        self.assertEqual(
            request.encode(certificateClient=0x123456.to_bytes(3, "big")), coded_request)

    def test_read_odx(self):
        expected = MinMaxLengthType(
            base_data_type="A_ASCIISTRING",
            base_type_encoding="ISO-8859-1",
            min_length=8,
            max_length=16,
            termination="ZERO",
            is_highlow_byte_order_raw=None,
        )

        # diag-coded-type requires xsi namespace
        diagcodedtype_odx = f"""
        <ODX xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <DIAG-CODED-TYPE BASE-TYPE-ENCODING="{expected.base_type_encoding}" BASE-DATA-TYPE="{expected.base_data_type.value}" TERMINATION="{expected.termination}" xsi:type="MIN-MAX-LENGTH-TYPE">
                <MIN-LENGTH>{expected.min_length}</MIN-LENGTH>
                <MAX-LENGTH>{expected.max_length}</MAX-LENGTH>
            </DIAG-CODED-TYPE>
        </ODX>
        """

        odx_element = ElementTree.fromstring(diagcodedtype_odx)
        diag_coded_type_element = odx_element.find("DIAG-CODED-TYPE")

        actual = create_any_diag_coded_type_from_et(diag_coded_type_element, doc_frags)

        self.assertIsInstance(actual, MinMaxLengthType)
        self.assertEqual(actual.base_data_type, expected.base_data_type)
        self.assertEqual(actual.base_type_encoding, expected.base_type_encoding)
        self.assertEqual(actual.min_length, expected.min_length)
        self.assertEqual(actual.max_length, expected.max_length)
        self.assertEqual(actual.termination, expected.termination)
        self.assertEqual(actual.is_highlow_byte_order, expected.is_highlow_byte_order)


if __name__ == "__main__":
    unittest.main()
