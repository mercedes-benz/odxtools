# SPDX-License-Identifier: MIT
import unittest
from xml.etree import ElementTree

from packaging.version import Version

import odxtools.uds as uds
from odxtools.compumethods.compucategory import CompuCategory
from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compurationalcoeffs import CompuRationalCoeffs
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.compumethods.linearcompumethod import LinearCompuMethod
from odxtools.createanydiagcodedtype import create_any_diag_coded_type_from_et
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.decodestate import DecodeState
from odxtools.description import Description
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.encodestate import EncodeState
from odxtools.encoding import Encoding
from odxtools.exceptions import DecodeError, EncodeError, OdxError, odxrequire
from odxtools.leadinglengthinfotype import LeadingLengthInfoType
from odxtools.minmaxlengthtype import MinMaxLengthType
from odxtools.nameditemlist import NamedItemList
from odxtools.odxdoccontext import OdxDocContext
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.lengthkeyparameter import LengthKeyParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.paramlengthinfotype import ParamLengthInfoType
from odxtools.physicaltype import PhysicalType
from odxtools.request import Request
from odxtools.standardlengthtype import StandardLengthType
from odxtools.termination import Termination

doc_frags = (OdxDocFragment("UnitTest", DocType.CONTAINER),)


class TestLeadingLengthInfoType(unittest.TestCase):

    def test_decode_leading_length_info_type_bytefield(self) -> None:
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_BYTEFIELD,
            bit_length=6,
        )
        state = DecodeState(bytes([0x2, 0x34, 0x56]), cursor_byte_position=0)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, bytes([0x34, 0x56]))

        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_BYTEFIELD,
            bit_length=5,
        )
        # 0xC2 = 0b11000010, with bit_position=1 and bit_lenth=5, the extracted bits are 00001,
        # i.e. the leading length is 1, i.e. only the byte 0x3 should be extracted.
        state = DecodeState(
            bytes([0x1, 0xC2, 0x3, 0x4]), cursor_byte_position=1, cursor_bit_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, bytes([0x3]))

    def test_decode_leading_length_info_type_zero_length(self) -> None:
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_BYTEFIELD,
            bit_length=8,
        )
        state = DecodeState(bytes([0x0, 0x1]), cursor_byte_position=0)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, b'')
        self.assertEqual(state.cursor_byte_position, 1)

    def test_encode_leading_length_info_type_bytefield(self) -> None:
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_BYTEFIELD,
            bit_length=5,
        )
        state = EncodeState(bytearray(), cursor_bit_position=3)
        dct.encode_into_pdu(bytes([0x3]), state)
        self.assertEqual(state.coded_message.hex(), "0803")

    def test_decode_leading_length_info_type_bytefield2(self) -> None:
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_BYTEFIELD,
            bit_length=5,
        )

        state = EncodeState(
            coded_message=bytearray.fromhex("0000ff00"),
            used_mask=bytearray.fromhex("0700ffff"),
            cursor_bit_position=3)
        dct.encode_into_pdu(bytes([0xcc]), state)
        self.assertEqual(state.coded_message.hex(), "08ccff00")
        self.assertEqual(state.cursor_byte_position, 2)
        self.assertEqual(state.cursor_bit_position, 0)

    def test_decode_leading_length_info_type_unicode2string(self) -> None:
        # big endian
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_UNICODE2STRING,
            bit_length=7,
        )
        state = DecodeState(
            bytes([0x12, 0x8, 0x00, 0x61, 0x00, 0x39, 0xff, 0x00]),
            cursor_byte_position=1,
            cursor_bit_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, "a9")
        self.assertEqual(state.cursor_byte_position, 6)
        self.assertEqual(state.cursor_bit_position, 0)

        # little endian
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_UNICODE2STRING,
            bit_length=8,
            is_highlow_byte_order_raw=False,
        )
        state = DecodeState(
            bytes([0x12, 0x4, 0x61, 0x00, 0x39, 0x00, 0xff, 0x00]), cursor_byte_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, "a9")
        self.assertEqual(state.cursor_byte_position, 6)
        self.assertEqual(state.cursor_bit_position, 0)

    def test_encode_leading_length_info_type_unicode2string(self) -> None:
        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_UNICODE2STRING,
            bit_length=8,
        )
        state = EncodeState(coded_message=bytearray())
        dct.encode_into_pdu("a9", state)
        self.assertEqual(state.coded_message, bytes([0x4, 0x00, 0x61, 0x00, 0x39]))

        dct = LeadingLengthInfoType(
            base_data_type=DataType.A_UNICODE2STRING,
            bit_length=8,
            is_highlow_byte_order_raw=False,
        )
        state = EncodeState(
            coded_message=bytearray(),
            cursor_byte_position=0,
            cursor_bit_position=0,
            origin_byte_position=0)
        dct.encode_into_pdu("a9", state)
        self.assertEqual(state.coded_message, bytes([0x4, 0x61, 0x00, 0x39, 0x00]))

    def test_end_to_end(self) -> None:
        # diag coded types
        diagcodedtypes = {
            "uint8":
                StandardLengthType(
                    base_data_type=DataType.A_UINT32,
                    bit_length=8,
                ),
            "certificateClient":
                LeadingLengthInfoType(
                    base_data_type=DataType.A_BYTEFIELD,
                    bit_length=8,
                ),
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
                IdenticalCompuMethod(
                    category=CompuCategory.IDENTICAL,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32),
            "bytes_passthrough":
                IdenticalCompuMethod(
                    category=CompuCategory.IDENTICAL,
                    internal_type=DataType.A_BYTEFIELD,
                    physical_type=DataType.A_BYTEFIELD),
        }

        # data object properties
        dops = {
            "certificateClient":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                    short_name="certificateClient",
                    diag_coded_type=diagcodedtypes["certificateClient"],
                    physical_type=PhysicalType(base_data_type=DataType.A_BYTEFIELD),
                    compu_method=compumethods["bytes_passthrough"],
                ),
        }

        # Request
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="SID",
                    semantic="SERVICE-ID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.UDSSID.Authentication.value),
                ),
                ValueParameter(
                    short_name="certificateClient",
                    description=Description.from_string("The certificate to verify."),
                    byte_position=1,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id),
                ),
            ]),
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=NamedItemList(dops.values())),
            requests=NamedItemList([request]),
        )
        ecu_variant = EcuVariant(diag_layer_raw=ecu_variant_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

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

    def test_decode_standard_length_type_uint(self) -> None:
        dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=5,
        )
        state = DecodeState(bytes([0x1, 0x72, 0x3]), cursor_byte_position=1, cursor_bit_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, 25)
        self.assertEqual(state.cursor_byte_position, 2)

    def test_decode_standard_length_type_uint_byteorder(self) -> None:
        dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=16,
            is_highlow_byte_order_raw=False,
        )
        state = DecodeState(bytes([0x1, 0x2, 0x3]), cursor_byte_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, 0x0302)
        self.assertEqual(state.cursor_byte_position, 3)

    def test_decode_standard_length_type_bytes(self) -> None:
        dct = StandardLengthType(
            base_data_type=DataType.A_BYTEFIELD,
            bit_length=16,
        )
        state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78]), cursor_byte_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, bytes([0x34, 0x56]))
        self.assertEqual(state.cursor_byte_position, 3)


class TestParamLengthInfoType(unittest.TestCase):

    def test_decode_param_info_length_type_uint(self) -> None:
        length_key_id = OdxLinkId("param.length_key", doc_frags)
        length_key_ref = OdxLinkRef.from_id(length_key_id)
        length_key = LengthKeyParameter(
            odx_id=length_key_id,
            short_name="length_key",
            dop_ref=OdxLinkRef("DOP.uint8", doc_frags),
            byte_position=1,
        )
        dct = ParamLengthInfoType(
            base_data_type=DataType.A_UINT32,
            length_key_ref=length_key_ref,
        )
        odxlinks = OdxLinkDatabase()
        odxlinks.update({length_key_id: length_key})
        dct._resolve_odxlinks(odxlinks)
        state = DecodeState(
            coded_message=bytes([0x10, 0x12, 0x34, 0x56]),
            length_keys={length_key.short_name: 16},
            cursor_byte_position=1,
        )
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, 0x1234)
        self.assertEqual(state.cursor_byte_position, 3)

    def test_encode_param_info_length_type_uint(self) -> None:
        length_key_id = OdxLinkId("param.length_key", doc_frags)
        length_key = LengthKeyParameter(
            odx_id=length_key_id,
            short_name="length_key",
            dop_ref=OdxLinkRef("DOP.uint8", doc_frags),
            byte_position=1,
        )
        dct = ParamLengthInfoType(
            base_data_type=DataType.A_UINT32,
            length_key_ref=OdxLinkRef.from_id(length_key_id),
        )
        odxlinks = OdxLinkDatabase()
        odxlinks.update({length_key_id: length_key})
        dct._resolve_odxlinks(odxlinks)
        state = EncodeState(coded_message=bytearray([0xcc]), cursor_byte_position=2)
        dct.encode_into_pdu(0x12345, state)
        self.assertEqual(state.coded_message.hex(), "cc00012345")
        self.assertEqual(state.length_keys.get("length_key"), 24)

    def test_end_to_end(self) -> None:
        # diag coded types
        diagcodedtypes = {
            "uint8":
                StandardLengthType(
                    base_data_type=DataType.A_UINT32,
                    bit_length=8,
                ),
            "length_key_id_to_lengthOfCertificateClient":
                ParamLengthInfoType(
                    base_data_type=DataType.A_UINT32,
                    length_key_ref=OdxLinkRef("param.dummy_length_key", doc_frags),
                ),
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
                IdenticalCompuMethod(
                    category=CompuCategory.IDENTICAL,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32),
            "multiply_with_8":
                LinearCompuMethod(
                    category=CompuCategory.LINEAR,
                    compu_internal_to_phys=CompuInternalToPhys(compu_scales=[
                        CompuScale(
                            compu_rational_coeffs=CompuRationalCoeffs(
                                value_type=DataType.A_INT32,
                                numerators=[0, 8],
                                denominators=[1],
                            ),
                            domain_type=DataType.A_INT32,
                            range_type=DataType.A_INT32),
                    ]),
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32,
                ),
        }

        # data object properties
        dops = {
            "uint8_times_8":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.uint8_times_8", doc_frags),
                    short_name="uint8_times_8",
                    diag_coded_type=diagcodedtypes["uint8"],
                    physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
                    compu_method=compumethods["multiply_with_8"],
                ),
            "certificateClient":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                    short_name="certificateClient",
                    diag_coded_type=diagcodedtypes["length_key_id_to_lengthOfCertificateClient"],
                    physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
                    compu_method=compumethods["uint_passthrough"],
                ),
        }

        # Request using LengthKeyParameter and ParamLengthInfoType
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="SID",
                    semantic="SERVICE-ID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.UDSSID.Authentication.value),
                ),
                LengthKeyParameter(
                    short_name="lengthOfCertificateClient",
                    description=Description.from_string("Length parameter for certificateClient."),
                    # LengthKeyParams have an ID to be referenced by a ParamLengthInfoType (which is a diag coded type)
                    odx_id=OdxLinkId("param.dummy_length_key", doc_frags),
                    byte_position=1,
                    # The DOP multiplies the coded value by 8, since the length key ref expects the number of bits.
                    dop_ref=OdxLinkRef.from_id(dops["uint8_times_8"].odx_id),
                ),
                ValueParameter(
                    short_name="certificateClient",
                    description=Description.from_string("The certificate to verify."),
                    byte_position=2,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id),
                ),
            ]),
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=NamedItemList(dops.values())),
            requests=NamedItemList([request]),
        )
        ecu_variant = EcuVariant(diag_layer_raw=ecu_variant_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

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

        # explicit defined length key
        encoded = request.encode(lengthOfCertificateClient=24, certificateClient=0x123456)
        self.assertEqual(encoded, coded_request)

        # Automatic bit length calculation
        encoded = request.encode(certificateClient=0x123456)
        self.assertEqual(encoded, coded_request)


class TestMinMaxLengthType(unittest.TestCase):

    def test_decode_min_max_length_type_bytes(self) -> None:
        dct = MinMaxLengthType(
            base_data_type=DataType.A_BYTEFIELD,
            min_length=1,
            max_length=4,
            termination=Termination.HEX_FF,
        )
        state = DecodeState(bytes([0x12, 0xFF, 0x34, 0x56, 0xFF]), cursor_byte_position=1)
        internal_value = dct.decode_from_pdu(state)
        self.assertEqual(internal_value, bytes([0xFF, 0x34, 0x56]))
        self.assertEqual(state.cursor_byte_position, 5)

    def test_decode_min_max_length_type_too_short_pdu(self) -> None:
        """If the PDU ends before min length is reached, an error must be raised."""
        dct = MinMaxLengthType(
            base_data_type=DataType.A_BYTEFIELD,
            min_length=2,
            max_length=4,
            termination=Termination.HEX_FF,
        )
        state = DecodeState(bytes([0x12, 0xFF]), cursor_byte_position=1)
        self.assertRaises(DecodeError, dct.decode_from_pdu, state)

    def test_decode_min_max_length_type_end_of_pdu(self) -> None:
        """If the PDU ends before max length is reached, the extracted value ends at the end of the PDU."""
        for termination in [Termination.END_OF_PDU, Termination.HEX_FF, Termination.ZERO]:
            dct = MinMaxLengthType(
                base_data_type=DataType.A_BYTEFIELD,
                min_length=2,
                max_length=5,
                termination=termination,
            )
            state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78, 0x9A]), cursor_byte_position=1)
            internal_value = dct.decode_from_pdu(state)
            self.assertEqual(internal_value, bytes([0x34, 0x56, 0x78, 0x9A]))
            self.assertEqual(state.cursor_byte_position, 5)

    def test_decode_min_max_length_type_max_length(self) -> None:
        """If the max length is smaller than the end of PDU, the extracted value ends after max length."""
        for termination in [Termination.END_OF_PDU, Termination.HEX_FF, Termination.ZERO]:
            dct = MinMaxLengthType(
                base_data_type=DataType.A_BYTEFIELD,
                min_length=2,
                max_length=3,
                termination=termination,
            )
            state = DecodeState(bytes([0x12, 0x34, 0x56, 0x78, 0x9A]), cursor_byte_position=1)
            internal_value = dct.decode_from_pdu(state)
            self.assertEqual(internal_value, bytes([0x34, 0x56, 0x78]))
            self.assertEqual(state.cursor_byte_position, 4)

    def test_encode_min_max_length_type_hex_ff(self) -> None:
        dct = MinMaxLengthType(
            base_data_type=DataType.A_BYTEFIELD,
            min_length=1,
            max_length=4,
            termination=Termination.HEX_FF,
        )
        state = EncodeState(is_end_of_pdu=False)
        dct.encode_into_pdu(bytes([0x34, 0x56]), state)
        self.assertEqual(state.coded_message, bytes([0x34, 0x56, 0xFF]))

    def test_encode_min_max_length_type_zero(self) -> None:
        dct = MinMaxLengthType(
            base_data_type=DataType.A_UTF8STRING,
            min_length=2,
            max_length=4,
            termination=Termination.ZERO,
        )
        state = EncodeState(is_end_of_pdu=False)
        dct.encode_into_pdu("Hi", state)
        self.assertEqual(state.coded_message, bytes([0x48, 0x69, 0x0]))

    def test_encode_min_max_length_type_end_of_pdu(self) -> None:
        """If the parameter is at the end of the PDU, no termination char is added."""
        for termination in [Termination.END_OF_PDU, Termination.HEX_FF, Termination.ZERO]:
            dct = MinMaxLengthType(
                base_data_type=DataType.A_BYTEFIELD,
                min_length=2,
                max_length=5,
                termination=termination,
            )
            state = EncodeState(coded_message=bytearray(), is_end_of_pdu=True)
            dct.encode_into_pdu(bytes([0x34, 0x56, 0x78, 0x9A]), state)
            self.assertEqual(state.coded_message.hex(), "3456789a")

            if termination == Termination.END_OF_PDU:
                state = EncodeState(coded_message=bytearray(), is_end_of_pdu=False)
                self.assertRaises(OdxError, dct.encode_into_pdu, bytes([0x34, 0x56, 0x78, 0x9A]),
                                  state)
            else:
                state = EncodeState(coded_message=bytearray(), is_end_of_pdu=False)
                dct.encode_into_pdu(bytes([0x34, 0x56, 0x78, 0x9A]), state)
                self.assertTrue(state.coded_message.hex().startswith("3456789a"))

    def test_encode_min_max_length_type_min_length(self) -> None:
        """If the internal value is smaller than min length, an EncodeError must be raised."""
        for termination in [Termination.END_OF_PDU, Termination.HEX_FF, Termination.ZERO]:
            dct = MinMaxLengthType(
                base_data_type=DataType.A_BYTEFIELD,
                min_length=2,
                max_length=3,
                termination=termination,
            )
            state = EncodeState(is_end_of_pdu=True)
            dct.encode_into_pdu(bytes([0x34, 0x56]), state)
            self.assertTrue(state.coded_message.hex().startswith("3456"))
            self.assertRaises(
                EncodeError,
                dct.encode_into_pdu,
                bytes([0x34]),
                state,
            )

    def test_encode_min_max_length_type_max_length(self) -> None:
        """If the internal value is larger than max length, an EncodeError must be raised."""
        for termination in [Termination.END_OF_PDU, Termination.HEX_FF, Termination.ZERO]:
            dct = MinMaxLengthType(
                base_data_type=DataType.A_BYTEFIELD,
                min_length=2,
                max_length=3,
                termination=termination,
            )
            state = EncodeState(is_end_of_pdu=True)
            dct.encode_into_pdu(bytes([0x34, 0x56, 0x78]), state)
            self.assertEqual(state.coded_message, bytes([0x34, 0x56, 0x78]))
            self.assertRaises(
                EncodeError,
                dct.encode_into_pdu,
                bytes([0x34, 0x56, 0x78, 0x9A]),
                state,
            )

    def test_end_to_end(self) -> None:
        # diag coded types
        diagcodedtypes = {
            "uint8":
                StandardLengthType(
                    base_data_type=DataType.A_UINT32,
                    bit_length=8,
                ),
            "certificateClient":
                MinMaxLengthType(
                    base_data_type=DataType.A_BYTEFIELD,
                    min_length=2,
                    max_length=10,
                    termination=Termination.ZERO,
                ),
        }

        # computation methods
        compumethods = {
            "uint_passthrough":
                IdenticalCompuMethod(
                    category=CompuCategory.IDENTICAL,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32),
            "bytes_passthrough":
                IdenticalCompuMethod(
                    category=CompuCategory.IDENTICAL,
                    internal_type=DataType.A_BYTEFIELD,
                    physical_type=DataType.A_BYTEFIELD),
        }

        # data object properties
        dops = {
            "certificateClient":
                DataObjectProperty(
                    odx_id=OdxLinkId("BV.dummy_DL.DOP.certificateClient", doc_frags),
                    short_name="certificateClient",
                    diag_coded_type=diagcodedtypes["certificateClient"],
                    physical_type=PhysicalType(base_data_type=DataType.A_BYTEFIELD),
                    compu_method=compumethods["bytes_passthrough"],
                ),
        }

        # Request
        request = Request(
            odx_id=OdxLinkId("BV.dummy_DL.RQ.sendCertificate", doc_frags),
            short_name="sendCertificate",
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="SID",
                    semantic="SERVICE-ID",
                    diag_coded_type=diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.UDSSID.Authentication.value),
                ),
                ValueParameter(
                    short_name="certificateClient",
                    description=Description.from_string("The certificate to verify."),
                    byte_position=1,
                    # This DOP references the above parameter lengthOfCertificateClient for the bit length.
                    dop_ref=OdxLinkRef.from_id(dops["certificateClient"].odx_id),
                ),
                CodedConstParameter(
                    short_name="dummy",
                    diag_coded_type=diagcodedtypes["uint8"],
                    coded_value_raw=str(0x99),
                ),
            ]),
        )

        # Dummy diag layer to resolve references from request parameters to DOPs
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("BV.dummy_DL", doc_frags),
            short_name="dummy_DL",
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=NamedItemList(dops.values())),
            requests=NamedItemList([request]),
        )
        ecu_variant = EcuVariant(diag_layer_raw=ecu_variant_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

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

    def test_read_odx(self) -> None:
        expected = MinMaxLengthType(
            base_data_type=DataType.A_ASCIISTRING,
            base_type_encoding=Encoding.ISO_8859_1,
            min_length=8,
            max_length=16,
            termination=Termination.ZERO,
        )

        # diag-coded-type requires xsi namespace
        diagcodedtype_odx = f"""
        <ODX xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <DIAG-CODED-TYPE BASE-TYPE-ENCODING="{expected.base_type_encoding and expected.base_type_encoding.value}" BASE-DATA-TYPE="{expected.base_data_type.value}" TERMINATION="{expected.termination.value}" xsi:type="MIN-MAX-LENGTH-TYPE">
                <MIN-LENGTH>{expected.min_length}</MIN-LENGTH>
                <MAX-LENGTH>{expected.max_length}</MAX-LENGTH>
            </DIAG-CODED-TYPE>
        </ODX>
        """

        odx_element = ElementTree.fromstring(diagcodedtype_odx)
        diag_coded_type_element = odxrequire(odx_element.find("DIAG-CODED-TYPE"))

        actual = create_any_diag_coded_type_from_et(diag_coded_type_element,
                                                    OdxDocContext(Version("2.2.0"), doc_frags))

        self.assertIsInstance(actual, MinMaxLengthType)
        assert isinstance(actual, MinMaxLengthType)
        assert isinstance(expected, MinMaxLengthType)
        self.assertEqual(actual.base_data_type, expected.base_data_type)
        self.assertEqual(actual.base_type_encoding, expected.base_type_encoding)
        self.assertEqual(actual.min_length, expected.min_length)
        self.assertEqual(actual.max_length, expected.max_length)
        self.assertEqual(actual.termination, expected.termination)
        self.assertEqual(actual.is_highlow_byte_order, expected.is_highlow_byte_order)


if __name__ == "__main__":
    unittest.main()
