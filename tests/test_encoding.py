# SPDX-License-Identifier: MIT
import math
import unittest
from datetime import datetime

from odxtools.compumethods.compucategory import CompuCategory
from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compurationalcoeffs import CompuRationalCoeffs
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.compumethods.linearcompumethod import LinearCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.decodestate import DecodeState
from odxtools.description import Description
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.diagnostictroublecode import DiagnosticTroubleCode
from odxtools.diagservice import DiagService
from odxtools.dtcdop import DtcDop
from odxtools.encodestate import EncodeState
from odxtools.encoding import Encoding
from odxtools.environmentdata import EnvironmentData
from odxtools.environmentdatadescription import EnvironmentDataDescription
from odxtools.exceptions import EncodeError, OdxError
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.nrcconstparameter import NrcConstParameter
from odxtools.parameters.parameter import Parameter
from odxtools.parameters.systemparameter import SystemParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.radix import Radix
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.snrefcontext import SnRefContext
from odxtools.standardlengthtype import StandardLengthType
from odxtools.text import Text

doc_frags = (OdxDocFragment("UnitTest", DocType.CONTAINER),)


class TestEncodeRequest(unittest.TestCase):

    def test_encode_coded_const_infer_order(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        param1 = CodedConstParameter(
            short_name="coded_const_parameter",
            diag_coded_type=diag_coded_type,
            coded_value_raw=str(0x7D),
            byte_position=0,
        )
        param2 = CodedConstParameter(
            short_name="coded_const_parameter",
            diag_coded_type=diag_coded_type,
            coded_value_raw=str(0xAB),
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList([param1, param2]),
        )
        self.assertEqual(req.encode(), bytearray([0x7D, 0xAB]))

    def test_string_encodings(self) -> None:
        # ISO 8859-1 (latin1)
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value="ä?a",
            bit_length=24,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.ISO_8859_1,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0xe4, 0x3f, 0x61]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.ISO_8859_1,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, "ä?a")

        # UTF-8
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value="ä?",
            bit_length=24,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.UTF8,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0xc3, 0xa4, 0x3f]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.UTF8,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, "ä?")

        # big-endian UTF-16
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value="ä",
            bit_length=16,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.UCS2,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x00, 0xe4]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=16,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.UCS2,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, "ä")

        # little-endian UTF-16
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value="ä",
            bit_length=16,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.UCS2,
            is_highlow_byte_order=False,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0xe4, 0x00]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=16,
            base_data_type=DataType.A_UTF8STRING,
            base_type_encoding=Encoding.UCS2,
            is_highlow_byte_order=False)
        self.assertEqual(decoded, "ä")

    def test_int_encodings(self) -> None:
        # packed BCD
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=1234,
            bit_length=24,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=Encoding.BCD_P,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x00, 0x12, 0x34]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=Encoding.BCD_P,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, 1234)

        # unpacked BCD
        encode_state = EncodeState()
        with self.assertRaises(OdxError):
            encode_state.emplace_atomic_value(
                internal_value=12,
                bit_length=24,
                base_data_type=DataType.A_INT32,
                base_type_encoding=Encoding.BCD_UP,
                is_highlow_byte_order=True,
                used_mask=None)
        encode_state.emplace_atomic_value(
            internal_value=12,
            bit_length=24,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=Encoding.BCD_UP,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x00, 0x01, 0x02]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=Encoding.BCD_UP,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, 12)

        # one complement
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=0x1234,
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.ONEC,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x00, 0x12, 0x34]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.ONEC,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, 0x1234)

        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=-0x1234,
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.ONEC,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0xff, 0xed, 0xcb]))

        decode_state = DecodeState(bytes(encode_state.coded_message))
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.ONEC,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, -0x1234)

        # two complement
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=0x1234,
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.TWOC,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x00, 0x12, 0x34]))

        decode_state = DecodeState(encode_state.coded_message)
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.TWOC,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, 0x1234)

        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=-0x1234,
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.TWOC,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0xff, 0xed, 0xcc]))

        decode_state = DecodeState(encode_state.coded_message)
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.TWOC,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, -0x1234)

        # sign-magnitude
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=0x1234,
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.SM,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x00, 0x12, 0x34]))

        decode_state = DecodeState(encode_state.coded_message)
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.SM,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, 0x1234)

        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=-0x1234,
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.SM,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, bytes([0x80, 0x12, 0x34]))

        decode_state = DecodeState(encode_state.coded_message)
        decoded = decode_state.extract_atomic_value(
            bit_length=24,
            base_data_type=DataType.A_INT32,
            base_type_encoding=Encoding.SM,
            is_highlow_byte_order=True)
        self.assertEqual(decoded, -0x1234)

    def test_float_encodings(self) -> None:
        # FLOAT32
        encode_state = EncodeState()
        with self.assertRaises(OdxError):
            encode_state.emplace_atomic_value(
                internal_value=-1.234,
                bit_length=24,
                base_data_type=DataType.A_FLOAT32,
                base_type_encoding=Encoding.NONE,
                is_highlow_byte_order=True,
                used_mask=None)
        encode_state.emplace_atomic_value(
            internal_value=-1.234,
            bit_length=32,
            base_data_type=DataType.A_FLOAT32,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, b'\xbf\x9d\xf3\xb6')

        decode_state = DecodeState(encode_state.coded_message)
        with self.assertRaises(OdxError):
            decoded = decode_state.extract_atomic_value(
                bit_length=24,
                base_data_type=DataType.A_FLOAT32,
                base_type_encoding=Encoding.NONE,
                is_highlow_byte_order=True)
        decoded = decode_state.extract_atomic_value(
            bit_length=32,
            base_data_type=DataType.A_FLOAT32,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=True)
        # allow rounding errors due to python's float objects
        # potentially using a different representation
        assert isinstance(decoded, float)
        self.assertTrue(abs(decoded - (-1.234)) < 1e-6)

        # FLOAT32 little-endian
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=-1.234,
            bit_length=32,
            base_data_type=DataType.A_FLOAT32,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=False,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, b'\xb6\xf3\x9d\xbf')

        decode_state = DecodeState(encode_state.coded_message)
        decoded = decode_state.extract_atomic_value(
            bit_length=32,
            base_data_type=DataType.A_FLOAT32,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=False)
        # allow rounding errors due to python's float objects
        # potentially using a different representation
        assert isinstance(decoded, float)
        self.assertTrue(abs(decoded - (-1.234)) < 1e-6)

        # check if NaN can be handled
        encode_state = EncodeState()
        encode_state.emplace_atomic_value(
            internal_value=float("nan"),
            bit_length=32,
            base_data_type=DataType.A_FLOAT32,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, b'\x7f\xc0\x00\x00')

        decode_state = DecodeState(encode_state.coded_message)
        decoded = decode_state.extract_atomic_value(
            bit_length=32,
            base_data_type=DataType.A_FLOAT32,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=True)
        assert isinstance(decoded, float)
        self.assertTrue(math.isnan(decoded))

        # FLOAT64
        encode_state = EncodeState()
        with self.assertRaises(OdxError):
            encode_state.emplace_atomic_value(
                internal_value=-1.234,
                bit_length=24,
                base_data_type=DataType.A_FLOAT64,
                base_type_encoding=Encoding.NONE,
                is_highlow_byte_order=True,
                used_mask=None)
        encode_state.emplace_atomic_value(
            internal_value=-1.234,
            bit_length=64,
            base_data_type=DataType.A_FLOAT64,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=True,
            used_mask=None)
        self.assertEqual(encode_state.coded_message, b'\xbf\xf3\xbev\xc8\xb49X')

        decode_state = DecodeState(encode_state.coded_message)
        with self.assertRaises(OdxError):
            decoded = decode_state.extract_atomic_value(
                bit_length=24,
                base_data_type=DataType.A_FLOAT64,
                base_type_encoding=Encoding.NONE,
                is_highlow_byte_order=True)
        decoded = decode_state.extract_atomic_value(
            bit_length=64,
            base_data_type=DataType.A_FLOAT64,
            base_type_encoding=Encoding.NONE,
            is_highlow_byte_order=True)
        # allow rounding errors due to python's float objects
        # potentially using a different representation
        assert isinstance(decoded, float)
        self.assertTrue(abs(decoded - (-1.234)) < 1e-9)

    def test_encode_coded_const_reorder(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        param1 = CodedConstParameter(
            short_name="param1",
            diag_coded_type=diag_coded_type,
            coded_value_raw=str(0x34),
            byte_position=1,
        )
        param2 = CodedConstParameter(
            short_name="param2",
            diag_coded_type=diag_coded_type,
            coded_value_raw=str(0x12),
            byte_position=0,
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList([param1, param2]),
        )
        self.assertEqual(req.encode(), bytearray([0x12, 0x34]))

    def test_encode_linear(self) -> None:
        odxlinks = OdxLinkDatabase()
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        # This CompuMethod represents the linear function: decode(x) = 2*x + 8 and encode(x) = (x-8)/2
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(compu_scales=[
                CompuScale(
                    compu_rational_coeffs=CompuRationalCoeffs(
                        value_type=DataType.A_INT32,
                        numerators=[8, 2],
                        denominators=[1],
                    ),
                    domain_type=DataType.A_INT32,
                    range_type=DataType.A_INT32),
            ]),
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            short_name="dop_sn",
            long_name="example dop",
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=compu_method,
        )
        odxlinks.update({dop.odx_id: dop})
        param1 = ValueParameter(
            short_name="value_parameter",
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
        )
        req = Request(
            odx_id=OdxLinkId("request.id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList([param1]),
        )

        snref_ctx = SnRefContext(parameters=req.parameters)
        param1._resolve_odxlinks(odxlinks)
        param1._resolve_snrefs(snref_ctx)

        # Missing mandatory parameter.
        with self.assertRaises(EncodeError):
            req.encode()

        self.assertEqual(
            req.encode(value_parameter=14),
            bytearray([0x3])  # encode(14) = (14-8)/2 = 3
        )

    def test_encode_nrc_const(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            short_name="dop_sn",
            long_name="example dop",
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
        )
        param1 = CodedConstParameter(
            short_name="param1",
            diag_coded_type=diag_coded_type,
            coded_value_raw=str(0x12),
            byte_position=0,
        )
        param2 = NrcConstParameter(
            short_name="param2",
            diag_coded_type=diag_coded_type,
            coded_values_raw=[str(0x34), str(0xAB)],
            byte_position=1,
        )
        param3 = ValueParameter(
            short_name="param3",
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            byte_position=1,
        )
        resp = Response(
            odx_id=OdxLinkId("response_id", doc_frags),
            short_name="response_sn",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([param1, param2, param3]),
        )

        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="req_param1",
                    diag_coded_type=diag_coded_type,
                    coded_value_raw=str(0xB0),
                    byte_position=0,
                )
            ]),
        )

        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            short_name="service_sn",
            request_ref=OdxLinkRef.from_id(req.odx_id),
            neg_response_refs=[OdxLinkRef.from_id(resp.odx_id)],
        )

        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("dl_id", doc_frags),
            short_name="dl_sn",
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=NamedItemList([dop])),
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            negative_responses=NamedItemList([resp]),
        )

        ecu_variant = EcuVariant(diag_layer_raw=ecu_variant_raw)
        db = Database()
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        with self.assertRaises(EncodeError):
            resp.encode()  # "No value for required parameter param3 specified"
        self.assertEqual(resp.encode(param3=0xAB).hex(), "12ab")
        with self.assertRaises(EncodeError):
            # Should raise an EncodeError because the value of
            # NRC-CONST parameters cannot be directly specified
            resp.encode(param2=0xEF, param3=0xAB)

    def test_encode_system_parameter(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=16,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.year", doc_frags),
            short_name="dop_year_sn",
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
        )
        param1 = SystemParameter(
            short_name="year_param",
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            sysparam="YEAR",
            byte_position=0,
        )

        odxlinks = OdxLinkDatabase()
        odxlinks.update(dop._build_odxlinks())

        param1._resolve_odxlinks(odxlinks)

        encode_state = EncodeState()
        param1.encode_into_pdu(physical_value=2024, encode_state=encode_state)
        self.assertEqual(encode_state.coded_message, b'\x07\xe8')

        # test auto-determination of parameter value
        cur_year = datetime.now().year
        encode_state = EncodeState()
        param1.encode_into_pdu(physical_value=None, encode_state=encode_state)

        # there is a (rather theoretical) race condition here: if the
        # cur_year variable was assigned before the year of the system
        # date changes (e.g., because it is new-year's eve) and the
        # encoding was done after that, we will get an incorrect value
        # here. (good luck exploiting this!)
        self.assertEqual(encode_state.coded_message, cur_year.to_bytes(2, 'big'))

        # ensure that decoding works as well
        decode_state = DecodeState(coded_message=encode_state.coded_message)
        self.assertEqual(param1.decode_from_pdu(decode_state), cur_year)

    def test_encode_env_data_desc(self) -> None:
        dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            short_name="dop_sn",
            long_name="example dop",
            diag_coded_type=dct,
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
        )

        dtc_dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=24,
        )
        dtc_dop = DtcDop(
            odx_id=OdxLinkId("dtcdop.id", doc_frags),
            short_name="dtcdop_sn",
            description=Description.from_string(
                "DOP containing all possible diagnostic trouble codes"),
            diag_coded_type=dtc_dct,
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32, display_radix=Radix.HEX),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            dtcs_raw=[
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DTCs.first_trouble", doc_frags),
                    short_name="first_trouble",
                    trouble_code=0x112233,
                    text=Text.from_string("The first trouble is the deepest"),
                    display_trouble_code="Z123"),
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DTCs.follow_up_trouble", doc_frags),
                    short_name="follow_up_trouble",
                    trouble_code=0x445566,
                    text=Text.from_string(""),
                    display_trouble_code="Y456"),
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DTCs.screwed_up_hard", doc_frags),
                    short_name="screwed_up_hard",
                    trouble_code=0xf00de5,
                    text=Text.from_string(""),
                    display_trouble_code="SCREW"),
            ],
        )

        env_data_desc = EnvironmentDataDescription(
            odx_id=OdxLinkId("DTCs.trouble_explanation", doc_frags),
            short_name="trouble_explanation",
            param_snref="DTC",
            env_datas=NamedItemList([
                EnvironmentData(
                    odx_id=OdxLinkId("DTCs.trouble_explanation.boiler_plate", doc_frags),
                    short_name="boiler_plate",
                    all_value=True,
                    parameters=NamedItemList([
                        CodedConstParameter(
                            short_name="blabla_boiler",
                            diag_coded_type=dct,
                            coded_value_raw=str(0xee),
                            byte_position=0,
                        )
                    ])),
                EnvironmentData(
                    odx_id=OdxLinkId("DTCs.trouble_explanation.reason_for_1", doc_frags),
                    short_name="reason_for_1",
                    dtc_values=[0x112233],
                    parameters=NamedItemList([
                        CodedConstParameter(
                            short_name="blabla_1",
                            diag_coded_type=dct,
                            coded_value_raw=str(0x01),
                        )
                    ])),
                EnvironmentData(
                    odx_id=OdxLinkId("DTCs.trouble_explanation.reason_for_2", doc_frags),
                    short_name="reason_for_2",
                    dtc_values=[0x445566],
                    parameters=NamedItemList([
                        CodedConstParameter(
                            short_name="blabla_3",
                            diag_coded_type=dct,
                            coded_value_raw=str(0x03),
                            byte_position=1,
                        ),
                        CodedConstParameter(
                            short_name="blabla_2",
                            diag_coded_type=dct,
                            coded_value_raw=str(0x02),
                            byte_position=0,
                        ),
                    ])),
            ]),
        )

        param1 = ValueParameter(
            short_name="DTC",
            dop_ref=OdxLinkRef.from_id(dtc_dop.odx_id),
        )
        param2 = ValueParameter(
            short_name="dtc_info",
            description=Description.from_string("Supplemental info why the error happened"),
            dop_ref=OdxLinkRef.from_id(env_data_desc.odx_id),
        )

        resp = Response(
            odx_id=OdxLinkId("DTCs.report_dtc.answer", doc_frags),
            short_name="report_dtc_answer",
            parameters=NamedItemList([param1, param2]),
            response_type=ResponseType.POSITIVE,
        )

        odxlinks = OdxLinkDatabase()
        odxlinks.update(dop._build_odxlinks())
        odxlinks.update(dtc_dop._build_odxlinks())
        odxlinks.update(env_data_desc._build_odxlinks())
        odxlinks.update(resp._build_odxlinks())

        dop._resolve_odxlinks(odxlinks)
        dtc_dop._resolve_odxlinks(odxlinks)
        env_data_desc._resolve_odxlinks(odxlinks)
        resp._resolve_odxlinks(odxlinks)

        snref_ctx = SnRefContext()

        dop._resolve_snrefs(snref_ctx)
        dtc_dop._resolve_snrefs(snref_ctx)
        env_data_desc._resolve_snrefs(snref_ctx)
        resp._resolve_snrefs(snref_ctx)

        # test environment data for DCT 0x112233
        raw_data = resp.encode(DTC=0x112233, dtc_info={})
        self.assertEqual(raw_data.hex(), "112233ee01")

        # test environment data for DCT 0x445566
        raw_data = resp.encode(DTC=0x445566, dtc_info={})
        self.assertEqual(raw_data.hex(), "445566ee0203")

        # test for a DCT without any special environment data (just
        # the all-data boiler plate)
        raw_data = resp.encode(DTC=0xf00de5, dtc_info={})
        self.assertEqual(raw_data.hex(), "f00de5ee")

        # test an unspecified DCT (raises EncodeError)
        with self.assertRaises(EncodeError):
            raw_data = resp.encode(DTC=0x00c007, dtc_info={})

    def test_encode_overlapping(self) -> None:
        uint24 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=24,
        )
        uint8 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        param1 = CodedConstParameter(
            short_name="code",
            diag_coded_type=uint24,
            coded_value_raw=str(0x123456),
            byte_position=0,
        )
        param2 = CodedConstParameter(
            short_name="part1",
            diag_coded_type=uint8,
            coded_value_raw=str(0x23),
            byte_position=0,
            bit_position=4,
        )
        param3 = CodedConstParameter(
            short_name="part2",
            diag_coded_type=uint8,
            coded_value_raw=str(0x45),
            byte_position=1,
            bit_position=4,
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList([param1, param2, param3]),
        )
        self.assertEqual(req.encode().hex(), "123456")
        self.assertEqual(req.get_static_bit_length(), 24)

    def _create_request(self, parameters: list[Parameter]) -> Request:
        return Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList(parameters),
        )

    def test_bit_mask(self) -> None:
        inner_dct = StandardLengthType(
            bit_mask=0x3fc, base_data_type=DataType.A_UINT32, bit_length=14)
        outer_dct = StandardLengthType(
            bit_mask=0xf00f, base_data_type=DataType.A_UINT32, bit_length=16)

        physical_type = PhysicalType(base_data_type=DataType.A_UINT32)
        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)

        inner_dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.inner', doc_frags),
            short_name="inner_dop",
            diag_coded_type=inner_dct,
            physical_type=physical_type,
            compu_method=compu_method)

        outer_dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.outer', doc_frags),
            short_name="outer_dop",
            diag_coded_type=outer_dct,
            physical_type=physical_type,
            compu_method=compu_method)

        odxlinks = OdxLinkDatabase()
        odxlinks.update(inner_dop._build_odxlinks())
        odxlinks.update(outer_dop._build_odxlinks())
        odxlinks.update(inner_dct._build_odxlinks())
        odxlinks.update(outer_dct._build_odxlinks())

        # Inner
        inner_param = ValueParameter(
            short_name="inner_param",
            byte_position=0,
            bit_position=2,
            dop_ref=OdxLinkRef.from_id(inner_dop.odx_id))
        snref_ctx = SnRefContext()
        inner_param._resolve_odxlinks(odxlinks)
        inner_param._resolve_snrefs(snref_ctx)

        # Outer
        outer_param = ValueParameter(
            short_name="outer_param", byte_position=0, dop_ref=OdxLinkRef.from_id(outer_dop.odx_id))
        outer_param._resolve_odxlinks(odxlinks)
        outer_param._resolve_snrefs(snref_ctx)

        req = self._create_request([inner_param, outer_param])

        # the bit shifts here stem from the fact that we placed the
        # inner parameter at bit position 2...
        self.assertEqual(req.encode(inner_param=0x1234 >> 2, outer_param=0x4568).hex(), "4238")
        self.assertEqual(
            req.decode(bytes.fromhex('abcd')), {
                "inner_param": (0xbc << 2),
                "outer_param": 0xa00d
            })

    def test_condensed_bit_mask(self) -> None:
        dct = StandardLengthType(
            bit_mask=0xf00f, base_data_type=DataType.A_UINT32, is_condensed_raw=True, bit_length=16)

        self.assertEqual(dct.get_static_bit_length(), 8)

        physical_type = PhysicalType(base_data_type=DataType.A_UINT32)
        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)

        dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.inner', doc_frags),
            short_name="dop",
            diag_coded_type=dct,
            physical_type=physical_type,
            compu_method=compu_method)

        odxlinks = OdxLinkDatabase()
        odxlinks.update(dop._build_odxlinks())
        odxlinks.update(dct._build_odxlinks())

        # Inner
        param = ValueParameter(
            short_name="param",
            byte_position=0,
            bit_position=2,
            dop_ref=OdxLinkRef.from_id(dop.odx_id))
        param._resolve_odxlinks(odxlinks)

        req = self._create_request([param])

        # the values here stem from the fact that we placed the
        # parameter at bit position 2...
        self.assertEqual(req.encode(param=0x1ff4).hex(), "000050")
        self.assertEqual(req.decode(bytes.fromhex('000050')), {
            "param": 0x1004,
        })


if __name__ == "__main__":
    unittest.main()
