# SPDX-License-Identifier: MIT
import unittest
from datetime import datetime
from typing import List

from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuCategory
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
from odxtools.environmentdata import EnvironmentData
from odxtools.environmentdatadescription import EnvironmentDataDescription
from odxtools.exceptions import EncodeError
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.nrcconstparameter import NrcConstParameter
from odxtools.parameters.parameter import Parameter
from odxtools.parameters.systemparameter import SystemParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaltype import PhysicalType, Radix
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.snrefcontext import SnRefContext
from odxtools.standardlengthtype import StandardLengthType

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestEncodeRequest(unittest.TestCase):

    def test_encode_coded_const_infer_order(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        param1 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x7D,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        param2 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0xAB,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            oid=None,
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1, param2]),
        )
        self.assertEqual(req.encode(), bytearray([0x7D, 0xAB]))

    def test_encode_coded_const_reorder(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        param1 = CodedConstParameter(
            oid=None,
            short_name="param1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x34,
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        param2 = CodedConstParameter(
            oid=None,
            short_name="param2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            oid=None,
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1, param2]),
        )
        self.assertEqual(req.encode(), bytearray([0x12, 0x34]))

    def test_encode_linear(self) -> None:
        odxlinks = OdxLinkDatabase()
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        # This CompuMethod represents the linear function: decode(x) = 2*x + 8 and encode(x) = (x-8)/2
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=None,
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            value_type=DataType.A_INT32,
                            numerators=[8, 2],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            oid=None,
            short_name="dop_sn",
            long_name="example dop",
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        odxlinks.update({dop.odx_id: dop})
        param1 = ValueParameter(
            oid=None,
            short_name="value_parameter",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request.id", doc_frags),
            oid=None,
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
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
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            oid=None,
            short_name="dop_sn",
            long_name="example dop",
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        param1 = CodedConstParameter(
            oid=None,
            short_name="param1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        param2 = NrcConstParameter(
            oid=None,
            short_name="param2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_values=[0x34, 0xAB],
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        param3 = ValueParameter(
            oid=None,
            short_name="param3",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        resp = Response(
            odx_id=OdxLinkId("response_id", doc_frags),
            oid=None,
            short_name="response_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([param1, param2, param3]),
        )

        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            oid=None,
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="req_param1",
                    long_name=None,
                    description=None,
                    semantic=None,
                    diag_coded_type=diag_coded_type,
                    coded_value=0xB0,
                    byte_position=0,
                    bit_position=None,
                    sdgs=[],
                )
            ]),
        )

        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            admin_data=None,
            semantic=None,
            audience=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[OdxLinkRef.from_id(resp.odx_id)],
            sdgs=[],
        )

        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("dl_id", doc_frags),
            oid=None,
            short_name="dl_sn",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(),
            functional_classes=NamedItemList(),
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                admin_data=None,
                dtc_dops=NamedItemList(),
                data_object_props=NamedItemList([dop]),
                structures=NamedItemList(),
                static_fields=NamedItemList(),
                end_of_pdu_fields=NamedItemList(),
                dynamic_length_fields=NamedItemList(),
                dynamic_endmarker_fields=NamedItemList(),
                tables=NamedItemList(),
                env_data_descs=NamedItemList(),
                env_datas=NamedItemList(),
                muxs=NamedItemList(),
                unit_spec=None,
                sdgs=[]),
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList([resp]),
            global_negative_responses=NamedItemList(),
            additional_audiences=NamedItemList(),
            import_refs=[],
            state_charts=NamedItemList(),
            sdgs=[],
            parent_refs=[],
            comparam_refs=[],
            ecu_variant_patterns=[],
            diag_variables_raw=[],
            variable_groups=NamedItemList(),
            libraries=NamedItemList(),
            dyn_defined_spec=None,
            sub_components=NamedItemList(),
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
            base_type_encoding=None,
            bit_length=16,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.year", doc_frags),
            oid=None,
            short_name="dop_year_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        param1 = SystemParameter(
            oid=None,
            short_name="year_param",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            sysparam="YEAR",
            byte_position=0,
            bit_position=None,
            sdgs=[],
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
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            oid=None,
            short_name="dop_sn",
            long_name="example dop",
            description=None,
            admin_data=None,
            diag_coded_type=dct,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )

        dtc_dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=24,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dtc_dop = DtcDop(
            odx_id=OdxLinkId("dtcdop.id", doc_frags),
            oid=None,
            short_name="dtcdop_sn",
            long_name=None,
            description=Description(
                "DOP containing all possible diagnostic trouble codes",
                external_docs=[],
                text_identifier=None),
            admin_data=None,
            sdgs=[],
            diag_coded_type=dtc_dct,
            physical_type=PhysicalType(
                base_data_type=DataType.A_UINT32, display_radix=Radix.HEX, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            dtcs_raw=[
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DTCs.first_trouble", doc_frags),
                    oid=None,
                    short_name="first_trouble",
                    long_name=None,
                    description=None,
                    trouble_code=0x112233,
                    text="The first trouble is the deepest",
                    display_trouble_code="Z123",
                    level=None,
                    is_temporary_raw=None,
                    sdgs=[]),
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DTCs.follow_up_trouble", doc_frags),
                    oid=None,
                    short_name="follow_up_trouble",
                    long_name=None,
                    description=None,
                    trouble_code=0x445566,
                    text=None,
                    display_trouble_code="Y456",
                    level=None,
                    is_temporary_raw=None,
                    sdgs=[]),
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DTCs.screwed_up_hard", doc_frags),
                    oid=None,
                    short_name="screwed_up_hard",
                    long_name=None,
                    description=None,
                    trouble_code=0xf00de5,
                    text=None,
                    display_trouble_code="SCREW",
                    level=None,
                    is_temporary_raw=None,
                    sdgs=[]),
            ],
            linked_dtc_dops_raw=[],
            is_visible_raw=None,
        )

        env_data_desc = EnvironmentDataDescription(
            odx_id=OdxLinkId("DTCs.trouble_explanation", doc_frags),
            oid=None,
            short_name="trouble_explanation",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            param_snref="DTC",
            param_snpathref=None,
            env_datas=NamedItemList([
                EnvironmentData(
                    odx_id=OdxLinkId("DTCs.trouble_explanation.boiler_plate", doc_frags),
                    oid=None,
                    short_name="boiler_plate",
                    long_name=None,
                    description=None,
                    admin_data=None,
                    sdgs=[],
                    byte_size=None,
                    all_value=True,
                    dtc_values=[],
                    parameters=NamedItemList([
                        CodedConstParameter(
                            oid=None,
                            short_name="blabla_boiler",
                            long_name=None,
                            description=None,
                            semantic=None,
                            diag_coded_type=dct,
                            coded_value=0xee,
                            byte_position=0,
                            bit_position=None,
                            sdgs=[],
                        )
                    ])),
                EnvironmentData(
                    odx_id=OdxLinkId("DTCs.trouble_explanation.reason_for_1", doc_frags),
                    oid=None,
                    short_name="reason_for_1",
                    long_name=None,
                    description=None,
                    admin_data=None,
                    sdgs=[],
                    byte_size=None,
                    all_value=None,
                    dtc_values=[0x112233],
                    parameters=NamedItemList([
                        CodedConstParameter(
                            oid=None,
                            short_name="blabla_1",
                            long_name=None,
                            description=None,
                            semantic=None,
                            diag_coded_type=dct,
                            coded_value=0x01,
                            byte_position=None,
                            bit_position=None,
                            sdgs=[],
                        )
                    ])),
                EnvironmentData(
                    odx_id=OdxLinkId("DTCs.trouble_explanation.reason_for_2", doc_frags),
                    oid=None,
                    short_name="reason_for_2",
                    long_name=None,
                    description=None,
                    admin_data=None,
                    sdgs=[],
                    byte_size=None,
                    all_value=None,
                    dtc_values=[0x445566],
                    parameters=NamedItemList([
                        CodedConstParameter(
                            oid=None,
                            short_name="blabla_3",
                            long_name=None,
                            description=None,
                            semantic=None,
                            diag_coded_type=dct,
                            coded_value=0x03,
                            byte_position=1,
                            bit_position=None,
                            sdgs=[],
                        ),
                        CodedConstParameter(
                            oid=None,
                            short_name="blabla_2",
                            long_name=None,
                            description=None,
                            semantic=None,
                            diag_coded_type=dct,
                            coded_value=0x02,
                            byte_position=0,
                            bit_position=None,
                            sdgs=[],
                        ),
                    ])),
            ]),
            env_data_refs=[],
        )

        param1 = ValueParameter(
            oid=None,
            short_name="DTC",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dtc_dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        param2 = ValueParameter(
            oid=None,
            short_name="dtc_info",
            long_name=None,
            description=Description(
                "Supplemental info why the error happened", external_docs=[], text_identifier=None),
            semantic=None,
            dop_ref=OdxLinkRef.from_id(env_data_desc.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )

        resp = Response(
            odx_id=OdxLinkId("DTCs.report_dtc.answer", doc_frags),
            oid=None,
            short_name="report_dtc_answer",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
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
            base_type_encoding=None,
            bit_length=24,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        uint8 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        param1 = CodedConstParameter(
            oid=None,
            short_name="code",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=uint24,
            coded_value=0x123456,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        param2 = CodedConstParameter(
            oid=None,
            short_name="part1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=uint8,
            coded_value=0x23,
            byte_position=0,
            bit_position=4,
            sdgs=[],
        )
        param3 = CodedConstParameter(
            oid=None,
            short_name="part2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=uint8,
            coded_value=0x45,
            byte_position=1,
            bit_position=4,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            oid=None,
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1, param2, param3]),
        )
        self.assertEqual(req.encode().hex(), "123456")
        self.assertEqual(req.get_static_bit_length(), 24)

    def _create_request(self, parameters: List[Parameter]) -> Request:
        return Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            oid=None,
            short_name="request_sn",
            parameters=NamedItemList(parameters),
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
        )

    def test_bit_mask(self) -> None:
        inner_dct = StandardLengthType(
            bit_mask=0x3fc,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
            bit_length=14)
        outer_dct = StandardLengthType(
            bit_mask=0xf00f,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
            bit_length=16)

        physical_type = PhysicalType(
            base_data_type=DataType.A_UINT32, display_radix=None, precision=None)
        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)

        inner_dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.inner', doc_frags),
            oid=None,
            short_name="inner_dop",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            diag_coded_type=inner_dct,
            physical_type=physical_type,
            compu_method=compu_method,
            unit_ref=None,
            internal_constr=None,
            physical_constr=None)

        outer_dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.outer', doc_frags),
            oid=None,
            short_name="outer_dop",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            diag_coded_type=outer_dct,
            physical_type=physical_type,
            compu_method=compu_method,
            unit_ref=None,
            internal_constr=None,
            physical_constr=None)

        odxlinks = OdxLinkDatabase()
        odxlinks.update(inner_dop._build_odxlinks())
        odxlinks.update(outer_dop._build_odxlinks())
        odxlinks.update(inner_dct._build_odxlinks())
        odxlinks.update(outer_dct._build_odxlinks())

        # Inner
        inner_param = ValueParameter(
            oid=None,
            short_name="inner_param",
            long_name=None,
            description=None,
            byte_position=0,
            bit_position=2,
            dop_ref=OdxLinkRef.from_id(inner_dop.odx_id),
            dop_snref=None,
            semantic=None,
            sdgs=[],
            physical_default_value_raw=None)
        snref_ctx = SnRefContext(parameters=[])
        inner_param._resolve_odxlinks(odxlinks)
        inner_param._resolve_snrefs(snref_ctx)

        # Outer
        outer_param = ValueParameter(
            oid=None,
            short_name="outer_param",
            long_name=None,
            description=None,
            byte_position=0,
            bit_position=None,
            dop_ref=OdxLinkRef.from_id(outer_dop.odx_id),
            dop_snref=None,
            semantic=None,
            sdgs=[],
            physical_default_value_raw=None)
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


if __name__ == "__main__":
    unittest.main()
