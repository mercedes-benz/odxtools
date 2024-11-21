# SPDX-License-Identifier: MIT
import unittest

from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuCategory
from odxtools.compumethods.compurationalcoeffs import CompuRationalCoeffs
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.compumethods.linearcompumethod import LinearCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.determinenumberofitems import DetermineNumberOfItems
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayers.basevariant import BaseVariant
from odxtools.diaglayers.basevariantraw import BaseVariantRaw
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.diagnostictroublecode import DiagnosticTroubleCode
from odxtools.diagservice import DiagService
from odxtools.dtcdop import DtcDop
from odxtools.dynamicendmarkerfield import DynamicEndmarkerField
from odxtools.dynamiclengthfield import DynamicLengthField
from odxtools.dynenddopref import DynEndDopRef
from odxtools.endofpdufield import EndOfPduField
from odxtools.exceptions import DecodeError, DecodeMismatch
from odxtools.message import Message
from odxtools.minmaxlengthtype import MinMaxLengthType
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType, ParameterValueDict
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.matchingrequestparameter import MatchingRequestParameter
from odxtools.parameters.nrcconstparameter import NrcConstParameter
from odxtools.parameters.physicalconstantparameter import PhysicalConstantParameter
from odxtools.parameters.reservedparameter import ReservedParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.snrefcontext import SnRefContext
from odxtools.standardlengthtype import StandardLengthType
from odxtools.staticfield import StaticField
from odxtools.structure import Structure

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestIdentifyingService(unittest.TestCase):

    def test_prefix_tree_construction(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        diag_coded_type_2 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=16,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x7D,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param2 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0xAB,
            byte_position=1,
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
            parameters=NamedItemList([req_param1, req_param2]),
        )
        odxlinks = OdxLinkDatabase()
        odxlinks.update({req.odx_id: req})
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
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
            sdgs=[],
        )

        req2_param2 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_3",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type_2,
            coded_value=0xCDE,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req2 = Request(
            odx_id=OdxLinkId("request_id2", doc_frags),
            oid=None,
            short_name="request_sn2",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req2_param2]),
        )
        odxlinks.update({req2.odx_id: req2})

        resp2_param2 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_4",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type_2,
            coded_value=0xC86,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        resp2 = Response(
            odx_id=OdxLinkId("response_id2", doc_frags),
            oid=None,
            short_name="response_sn2",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([req_param1, resp2_param2]),
        )
        odxlinks.update({resp2.odx_id: resp2})

        service2 = DiagService(
            odx_id=OdxLinkId("service_id2", doc_frags),
            oid=None,
            short_name="service_sn2",
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
            request_ref=OdxLinkRef.from_id(req2.odx_id),
            pos_response_refs=[OdxLinkRef.from_id(resp2.odx_id)],
            neg_response_refs=[],
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
            diag_data_dictionary_spec=None,
            diag_comms_raw=[service, service2],
            requests=NamedItemList([req, req2]),
            positive_responses=NamedItemList([resp2]),
            negative_responses=NamedItemList(),
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
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        self.assertEqual(
            ecu_variant._prefix_tree,
            {0x7D: {
                0xAB: {
                    -1: [service]
                },
                0xC: {
                    0xDE: {
                        -1: [service2]
                    },
                    0x86: {
                        -1: [service2]
                    }
                }
            }},
        )


class TestDecoding(unittest.TestCase):

    def test_decode_request_coded_const(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x7D,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param2 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0xAB,
            byte_position=1,
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
            parameters=NamedItemList([req_param1, req_param2]),
        )

        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
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
            diag_data_dictionary_spec=None,
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        coded_message = bytes([0x7D, 0xAB])
        expected_message = Message(
            coded_message=coded_message,
            service=service,
            coding_object=req,
            param_dict={
                "SID": 0x7D,
                "coded_const_parameter_2": 0xAB
            },
        )
        decoded_message = ecu_variant.decode(coded_message)[0]

        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_decode_nrc_const(self) -> None:
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

        base_variant_raw = BaseVariantRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
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
            diag_variables_raw=[],
            variable_groups=NamedItemList(),
            libraries=NamedItemList(),
            dyn_defined_spec=None,
            sub_components=NamedItemList(),
        )
        ecu_variant = BaseVariant(diag_layer_raw=base_variant_raw)
        db = Database()
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        decoded = resp.decode(bytes.fromhex("12ab"))
        self.assertEqual(decoded, {'param1': 0x12, 'param2': 0xab, 'param3': 0xab})

        decoded = resp.decode(bytes.fromhex("1234"))
        self.assertEqual(decoded, {'param1': 0x12, 'param2': 0x34, 'param3': 0x34})

        with self.assertRaises(DecodeMismatch):
            decoded = resp.decode(bytes.fromhex("12bc"))

        decoded_list = ecu_variant.decode_response(bytes.fromhex("12ab"), bytes.fromhex("B0"))
        self.assertEqual(len(decoded_list), 1)
        self.assertEqual(decoded_list[0].param_dict, {
            'param1': 0x12,
            'param2': 0xab,
            'param3': 0xab
        })

        with self.assertRaises(DecodeError):
            decoded_list = ecu_variant.decode_response(bytes.fromhex("12bc"), bytes.fromhex("B0"))

    def test_decode_request_coded_const_undefined_byte_position(self) -> None:
        """Test decoding of parameter
        Test if the decoding works if the byte position of the second parameter
        must be inferred from the order in the surrounding structure."""
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param2 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x78,
            byte_position=3,
            bit_position=None,
            sdgs=[],
        )
        req_param3 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_3",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x34,
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        req_param4 = CodedConstParameter(
            oid=None,
            short_name="coded_const_parameter_4",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x56,
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
            parameters=NamedItemList([req_param1, req_param2, req_param3, req_param4]),
        )

        odxlinks = OdxLinkDatabase()
        odxlinks.update({req.odx_id: req})
        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
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
            diag_data_dictionary_spec=None,
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
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
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        self.assertDictEqual(ecu_variant._prefix_tree,
                             {0x12: {
                                 0x34: {
                                     0x56: {
                                         0x78: {
                                             -1: [service]
                                         }
                                     }
                                 }
                             }})

        coded_message = bytes([0x12, 0x34, 0x56, 0x78])
        expected_message = Message(
            coded_message=coded_message,
            service=service,
            coding_object=req,
            param_dict={
                "SID": 0x12,
                "coded_const_parameter_2": 0x78,
                "coded_const_parameter_3": 0x34,
                "coded_const_parameter_4": 0x56,
            },
        )
        decoded_message = ecu_variant.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_decode_request_structure(self) -> None:
        """Test the decoding for a structure."""
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        diag_coded_type_4 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=4,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )

        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.odx_id", doc_frags),
            oid=None,
            short_name="dop_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type_4,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )

        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )

        struct_param1 = CodedConstParameter(
            oid=None,
            short_name="struct_param_1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type_4,
            coded_value=0x4,
            byte_position=0,
            bit_position=0,
            sdgs=[],
        )
        struct_param2 = ValueParameter(
            oid=None,
            short_name="struct_param_2",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=0,
            bit_position=4,
            sdgs=[],
        )
        struct = Structure(
            odx_id=OdxLinkId("struct_id", doc_frags),
            oid=None,
            short_name="struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([struct_param1, struct_param2]),
            byte_size=None,
        )
        req_param2 = ValueParameter(
            oid=None,
            short_name="structured_param",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(struct.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
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
            parameters=NamedItemList([req_param1, req_param2]),
        )
        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
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
                structures=NamedItemList([struct]),
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
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        coded_message = bytes([0x12, 0x34])
        expected_message = Message(
            coded_message=coded_message,
            service=service,
            coding_object=req,
            param_dict={
                "SID": 0x12,
                "structured_param": {
                    "struct_param_1": 4,
                    "struct_param_2": 3
                },
            },
        )
        decoded_message = ecu_variant.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_static_field_coding(self) -> None:
        """Test en- and decoding of static fields."""
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )

        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("static_field.dop.id", doc_frags),
            oid=None,
            short_name="static_field_dop_sn",
            long_name=None,
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

        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )

        struct_param1 = ValueParameter(
            oid=None,
            short_name="static_field_struct_param_1",
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
        struct_param2 = ValueParameter(
            oid=None,
            short_name="static_field_struct_param_2",
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
        struct = Structure(
            odx_id=OdxLinkId("static_field_struct.id", doc_frags),
            oid=None,
            short_name="static_field_struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([struct_param1, struct_param2]),
            byte_size=None,
        )
        static_field = StaticField(
            odx_id=OdxLinkId("static_field.id", doc_frags),
            oid=None,
            short_name="static_field_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            structure_ref=OdxLinkRef.from_id(struct.odx_id),
            structure_snref=None,
            env_data_desc_ref=None,
            env_data_desc_snref=None,
            is_visible_raw=True,
            fixed_number_of_items=2,
            item_byte_size=3,
        )
        req_param2 = ValueParameter(
            oid=None,
            short_name="static_field_param",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(static_field.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )

        req = Request(
            odx_id=OdxLinkId("static_field.request.id", doc_frags),
            oid=None,
            short_name="static_field_request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2]),
        )
        service = DiagService(
            odx_id=OdxLinkId("static_field.service.id", doc_frags),
            oid=None,
            short_name="static_field_service_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
            sdgs=[],
        )
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("dl.id", doc_frags),
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
                structures=NamedItemList([struct]),
                end_of_pdu_fields=NamedItemList(),
                dynamic_length_fields=NamedItemList(),
                dynamic_endmarker_fields=NamedItemList(),
                static_fields=NamedItemList([static_field]),
                tables=NamedItemList(),
                env_data_descs=NamedItemList(),
                env_datas=NamedItemList(),
                muxs=NamedItemList(),
                unit_spec=None,
                sdgs=[]),
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        expected_message = Message(
            coded_message=bytes([0x12, 0x34, 0x56, 0x00, 0x78, 0x9a, 0x00]),
            service=service,
            coding_object=req,
            param_dict={
                "SID":
                    0x12,
                "static_field_param": [
                    {
                        "static_field_struct_param_1": 0x34,
                        "static_field_struct_param_2": 0x56
                    },
                    {
                        "static_field_struct_param_1": 0x78,
                        "static_field_struct_param_2": 0x9a
                    },
                ],
            },
        )

        # test encoding
        encoded_message = ecu_variant.services.static_field_service_sn(
            **expected_message.param_dict)
        self.assertEqual(encoded_message, expected_message.coded_message)

        # test decoding
        decoded_message = ecu_variant.decode(expected_message.coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_dynamic_endmarker_field_coding(self) -> None:
        """Test en- and decoding of dynamic endmarker fields."""
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        diag_coded_type_4 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=4,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        diag_coded_endmarker_type = StandardLengthType(
            base_data_type=DataType.A_BYTEFIELD,
            base_type_encoding=None,
            bit_length=24,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )

        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)
        compu_method_bytefield = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_BYTEFIELD,
            physical_type=DataType.A_BYTEFIELD)

        dop = DataObjectProperty(
            odx_id=OdxLinkId("demf.dop.id", doc_frags),
            oid=None,
            short_name="demf_dop_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type_4,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        dyn_end_dop = DataObjectProperty(
            odx_id=OdxLinkId("demf.end_dop.id", doc_frags),
            oid=None,
            short_name="demf_end_dop_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_endmarker_type,
            physical_type=PhysicalType(DataType.A_BYTEFIELD, display_radix=None, precision=None),
            compu_method=compu_method_bytefield,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        dyn_end_dop_ref = DynEndDopRef(
            termination_value_raw="ffffff",
            ref_id=dyn_end_dop.odx_id.local_id,
            ref_docs=dyn_end_dop.odx_id.doc_fragments,
        )

        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param1_1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x13,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )

        struct_param1 = CodedConstParameter(
            oid=None,
            short_name="struct_param_1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type_4,
            coded_value=0x4,
            byte_position=0,
            bit_position=0,
            sdgs=[],
        )
        struct_param2 = ValueParameter(
            oid=None,
            short_name="struct_param_2",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=0,
            bit_position=4,
            sdgs=[],
        )
        struct = Structure(
            odx_id=OdxLinkId("demf_struct.id", doc_frags),
            oid=None,
            short_name="demf_struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([struct_param1, struct_param2]),
            byte_size=None,
        )
        demf = DynamicEndmarkerField(
            odx_id=OdxLinkId("demf.id", doc_frags),
            oid=None,
            short_name="demf_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            structure_ref=OdxLinkRef.from_id(struct.odx_id),
            structure_snref=None,
            env_data_desc_ref=None,
            env_data_desc_snref=None,
            is_visible_raw=True,
            dyn_end_dop_ref=dyn_end_dop_ref,
        )
        req_param2 = ValueParameter(
            oid=None,
            short_name="demf_param",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(demf.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req_demf_endmarker_param = ReservedParameter(
            oid=None,
            short_name="demf_endmarker",
            long_name=None,
            description=None,
            semantic=None,
            bit_length=24,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req_param3 = CodedConstParameter(
            oid=None,
            short_name="demf_post_param",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0xcc,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )

        req = Request(
            odx_id=OdxLinkId("demf.request.id", doc_frags),
            oid=None,
            short_name="demf_request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2, req_demf_endmarker_param,
                                      req_param3]),
        )

        # same as the previous request, but the dynamic endmarker
        # field is at the end of the PDU, so no endmarker is added
        req_end_of_pdu = Request(
            odx_id=OdxLinkId("demf_eopdu.request.id", doc_frags),
            oid=None,
            short_name="demf_eopdu_request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1_1, req_param2]),
        )

        service = DiagService(
            odx_id=OdxLinkId("demf.service.id", doc_frags),
            oid=None,
            short_name="demf_service_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
            sdgs=[],
        )
        service_eopdu = DiagService(
            odx_id=OdxLinkId("demf.service_eopdu.id", doc_frags),
            oid=None,
            short_name="demf_service_eopdu_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req_end_of_pdu.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
            sdgs=[],
        )
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("dl.id", doc_frags),
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
                data_object_props=NamedItemList([dop, dyn_end_dop]),
                structures=NamedItemList([struct]),
                end_of_pdu_fields=NamedItemList(),
                dynamic_length_fields=NamedItemList(),
                dynamic_endmarker_fields=NamedItemList([demf]),
                static_fields=NamedItemList(),
                tables=NamedItemList(),
                env_data_descs=NamedItemList(),
                env_datas=NamedItemList(),
                muxs=NamedItemList(),
                unit_spec=None,
                sdgs=[]),
            diag_comms_raw=[service, service_eopdu],
            requests=NamedItemList([req, req_end_of_pdu]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        ######
        ## test with endmarker termination
        expected_message = Message(
            coded_message=bytes([0x12, 0x34, 0x44, 0x54, 0xff, 0xff, 0xff, 0xcc]),
            service=service,
            coding_object=req,
            param_dict={
                "SID": 0x12,
                "demf_param": [
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 3
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 4
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 5
                    },
                ],
                "demf_endmarker": 0xffffff,
                "demf_post_param": 0xcc,
            },
        )

        # test encoding
        encoded_message = ecu_variant.services.demf_service_sn(**expected_message.param_dict)
        self.assertEqual(encoded_message, expected_message.coded_message)

        # test decoding
        decoded_message = ecu_variant.decode(expected_message.coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

        ######
        ## test with end-of-pdu termination
        expected_message_eopdu = Message(
            coded_message=bytes([0x13, 0x34, 0x44, 0x54]),
            service=service_eopdu,
            coding_object=req_end_of_pdu,
            param_dict={
                "SID":
                    0x13,
                "demf_param": [
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 3
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 4
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 5
                    },
                ],
            },
        )

        # test encoding
        encoded_message = ecu_variant.services.demf_service_eopdu_sn(
            **expected_message_eopdu.param_dict)
        self.assertEqual(encoded_message, expected_message_eopdu.coded_message)

        # test decoding
        decoded_message = ecu_variant.decode(expected_message_eopdu.coded_message)[0]
        self.assertEqual(expected_message_eopdu.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message_eopdu.service, decoded_message.service)
        self.assertEqual(expected_message_eopdu.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message_eopdu.param_dict, decoded_message.param_dict)

    def test_dynamic_length_field_coding(self) -> None:
        """Test en- and decoding of dynamic length fields."""
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        diag_coded_type_4 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=4,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )

        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dlf.dop.id", doc_frags),
            oid=None,
            short_name="dlf_dop_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type_4,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )

        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )

        struct_param1 = CodedConstParameter(
            oid=None,
            short_name="struct_param_1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type_4,
            coded_value=0x4,
            byte_position=0,
            bit_position=0,
            sdgs=[],
        )
        struct_param2 = ValueParameter(
            oid=None,
            short_name="struct_param_2",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=0,
            bit_position=4,
            sdgs=[],
        )
        struct = Structure(
            odx_id=OdxLinkId("dlf_struct.id", doc_frags),
            oid=None,
            short_name="dlf_struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([struct_param1, struct_param2]),
            byte_size=None,
        )
        det_num_items = DetermineNumberOfItems(
            byte_position=1, bit_position=3, dop_ref=OdxLinkRef.from_id(dop.odx_id))
        dlf = DynamicLengthField(
            odx_id=OdxLinkId("dlf.id", doc_frags),
            oid=None,
            short_name="dlf_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            structure_ref=OdxLinkRef.from_id(struct.odx_id),
            structure_snref=None,
            env_data_desc_ref=None,
            env_data_desc_snref=None,
            is_visible_raw=True,
            offset=3,
            determine_number_of_items=det_num_items,
        )
        req_param2 = ValueParameter(
            oid=None,
            short_name="dlf_param",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dlf.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )

        req = Request(
            odx_id=OdxLinkId("dlf.request.id", doc_frags),
            oid=None,
            short_name="dlf_request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2]),
        )
        service = DiagService(
            odx_id=OdxLinkId("dlf.service.id", doc_frags),
            oid=None,
            short_name="dlf_service_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
            sdgs=[],
        )
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("dl.id", doc_frags),
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
                structures=NamedItemList([struct]),
                end_of_pdu_fields=NamedItemList(),
                dynamic_length_fields=NamedItemList([dlf]),
                dynamic_endmarker_fields=NamedItemList(),
                static_fields=NamedItemList(),
                tables=NamedItemList(),
                env_data_descs=NamedItemList(),
                env_datas=NamedItemList(),
                muxs=NamedItemList(),
                unit_spec=None,
                sdgs=[]),
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        expected_message = Message(
            coded_message=bytes([0x12, 0x00, 0x18, 0x00, 0x34, 0x44, 0x54]),
            service=service,
            coding_object=req,
            param_dict={
                "SID":
                    0x12,
                "dlf_param": [
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 3
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 4
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 5
                    },
                ],
            },
        )

        # test encoding
        encoded_message = ecu_variant.services.dlf_service_sn(**expected_message.param_dict)
        self.assertEqual(encoded_message, expected_message.coded_message)

        # test decoding
        decoded_message = ecu_variant.decode(expected_message.coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_decode_request_end_of_pdu_field(self) -> None:
        """Test decoding of end-of-pdu fields."""
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        diag_coded_type_4 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=4,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )

        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            oid=None,
            short_name="dop_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type_4,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )

        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )

        struct_param1 = CodedConstParameter(
            oid=None,
            short_name="struct_param_1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type_4,
            coded_value=0x4,
            byte_position=0,
            bit_position=0,
            sdgs=[],
        )
        struct_param2 = ValueParameter(
            oid=None,
            short_name="struct_param_2",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=0,
            bit_position=4,
            sdgs=[],
        )
        struct = Structure(
            odx_id=OdxLinkId("struct_id", doc_frags),
            oid=None,
            short_name="struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([struct_param1, struct_param2]),
            byte_size=None,
        )
        eopf = EndOfPduField(
            odx_id=OdxLinkId("eopf_id", doc_frags),
            oid=None,
            short_name="eopf_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            structure_ref=OdxLinkRef.from_id(struct.odx_id),
            structure_snref=None,
            env_data_desc_ref=None,
            env_data_desc_snref=None,
            min_number_of_items=None,
            max_number_of_items=None,
            is_visible_raw=True,
        )
        req_param2 = ValueParameter(
            oid=None,
            short_name="eopf_param",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(eopf.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
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
            parameters=NamedItemList([req_param1, req_param2]),
        )
        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            admin_data=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
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
                structures=NamedItemList([struct]),
                static_fields=NamedItemList(),
                end_of_pdu_fields=NamedItemList([eopf]),
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
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        coded_message = bytes([0x12, 0x34, 0x54])
        expected_message = Message(
            coded_message=coded_message,
            service=service,
            coding_object=req,
            param_dict={
                "SID":
                    0x12,
                "eopf_param": [
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 3
                    },
                    {
                        "struct_param_1": 4,
                        "struct_param_2": 5
                    },
                ],
            },
        )
        decoded_message = ecu_variant.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_decode_request_linear_compu_method(self) -> None:
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
                            numerators=[1, 5],
                            denominators=[1],
                        ),
                        domain_type=DataType.A_INT32,
                        range_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32,
        )
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("linear.dop.id", doc_frags),
            oid=None,
            short_name="linear_dop_sn",
            long_name=None,
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
        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x7D,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param2 = ValueParameter(
            oid=None,
            short_name="value_parameter_2",
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
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            oid=None,
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2]),
        )

        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[],
            neg_response_refs=[],
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
            negative_responses=NamedItemList(),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        coded_message = bytes([0x7D, 0x12])
        # The physical value of the second parameter is decode(0x12) = decode(18) = 5 * 18 + 1 = 91
        expected_message = Message(
            coded_message=coded_message,
            service=service,
            coding_object=req,
            param_dict={
                "SID": 0x7D,
                "value_parameter_2": 91
            },
        )
        decoded_message = ecu_variant.decode(coded_message)[0]
        self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
        self.assertEqual(expected_message.service, decoded_message.service)
        self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
        self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_decode_response(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param2 = CodedConstParameter(
            oid=None,
            short_name="req_param",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0xAB,
            byte_position=1,
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
            parameters=NamedItemList([req_param1, req_param2]),
        )

        resp_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x34,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        resp_param2 = MatchingRequestParameter(
            oid=None,
            short_name="matching_req_param",
            long_name=None,
            description=None,
            semantic=None,
            request_byte_position=1,
            byte_length=1,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        pos_response = Response(
            odx_id=OdxLinkId("pos_response_id", doc_frags),
            oid=None,
            short_name="pos_response_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([resp_param1, resp_param2]),
        )

        resp_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x56,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        resp_param2 = MatchingRequestParameter(
            oid=None,
            short_name="matching_req_param",
            long_name=None,
            description=None,
            semantic=None,
            request_byte_position=1,
            byte_length=1,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        neg_response = Response(
            odx_id=OdxLinkId("neg_response_id", doc_frags),
            oid=None,
            short_name="neg_response_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([resp_param1, resp_param2]),
        )

        service = DiagService(
            odx_id=OdxLinkId("service_id", doc_frags),
            oid=None,
            short_name="service_sn",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            semantic=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(req.odx_id),
            pos_response_refs=[OdxLinkRef.from_id(pos_response.odx_id)],
            neg_response_refs=[OdxLinkRef.from_id(neg_response.odx_id)],
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
            diag_data_dictionary_spec=None,
            diag_comms_raw=[service],
            requests=NamedItemList([req]),
            positive_responses=NamedItemList([pos_response]),
            negative_responses=NamedItemList([neg_response]),
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
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        db = Database()
        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        for sid, message in [(0x34, pos_response), (0x56, neg_response)]:
            coded_message = bytes([sid, 0xAB])
            expected_message = Message(
                coded_message=coded_message,
                service=service,
                coding_object=message,
                param_dict={
                    "SID": sid,
                    "matching_req_param": 0xAB
                },
            )
            decoded_message = ecu_variant.decode(coded_message)[0]
            self.assertEqual(expected_message.coded_message, decoded_message.coded_message)
            self.assertEqual(expected_message.service, decoded_message.service)
            self.assertEqual(expected_message.coding_object, decoded_message.coding_object)
            self.assertEqual(expected_message.param_dict, decoded_message.param_dict)

    def test_code_dtc(self) -> None:
        odxlinks = OdxLinkDatabase()
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32)

        dtc1 = DiagnosticTroubleCode(
            odx_id=OdxLinkId("dtcID1", doc_frags),
            oid=None,
            short_name="P34_sn",
            long_name=None,
            description=None,
            trouble_code=0x34,
            text="Error encountered",
            display_trouble_code="P34",
            level=None,
            is_temporary_raw=None,
            sdgs=[],
        )

        dtc2 = DiagnosticTroubleCode(
            odx_id=OdxLinkId("dtcID2", doc_frags),
            oid=None,
            short_name="P56_sn",
            long_name=None,
            description=None,
            trouble_code=0x56,
            text="Crashed into wall",
            display_trouble_code="P56",
            level=None,
            is_temporary_raw=None,
            sdgs=[],
        )
        dop = DtcDop(
            odx_id=OdxLinkId("dtc.dop.odx_id", doc_frags),
            oid=None,
            short_name="dtc_dop_sn",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            linked_dtc_dops_raw=[],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            dtcs_raw=[dtc1, dtc2],
            sdgs=[],
            is_visible_raw=None,
        )
        odxlinks.update(dop._build_odxlinks())
        resp_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        resp_param2 = ValueParameter(
            oid=None,
            short_name="DTC_Param",
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
        pos_response = Response(
            odx_id=OdxLinkId("pos_response_id", doc_frags),
            oid=None,
            short_name="pos_response_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([resp_param1, resp_param2]),
            response_type=ResponseType.POSITIVE,
        )
        odxlinks.update(pos_response._build_odxlinks())

        dop._resolve_odxlinks(odxlinks)
        pos_response._resolve_odxlinks(odxlinks)

        expected_coded_message = bytes([0x12, 0x34])
        expected_param_dict: ParameterValueDict = {"SID": 0x12, "DTC_Param": dtc1}

        actual_param_dict = pos_response.decode(expected_coded_message)
        self.assertEqual(actual_param_dict, expected_param_dict)

        actual_coded_message = pos_response.encode(coded_request=None, **expected_param_dict)
        self.assertEqual(actual_coded_message, expected_coded_message)


class TestDecodingAndEncoding(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        odxlinks = OdxLinkDatabase()
        self.dop_bytes_termination_end_of_pdu = DataObjectProperty(
            odx_id=OdxLinkId("DOP_ID", doc_frags),
            oid=None,
            short_name="DOP",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=MinMaxLengthType(
                base_data_type=DataType.A_BYTEFIELD,
                min_length=0,
                max_length=None,
                termination="END-OF-PDU",
                base_type_encoding=None,
                is_highlow_byte_order_raw=None,
            ),
            physical_type=PhysicalType(DataType.A_BYTEFIELD, display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_BYTEFIELD,
                physical_type=DataType.A_BYTEFIELD),
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        dop = self.dop_bytes_termination_end_of_pdu
        odxlinks.update(dop._build_odxlinks())
        self.parameter_termination_end_of_pdu = ValueParameter(
            oid=None,
            short_name="min_max_parameter",
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

        self.parameter_sid = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=StandardLengthType(
                base_data_type=DataType.A_UINT32,
                bit_length=8,
                bit_mask=None,
                base_type_encoding=None,
                is_condensed_raw=None,
                is_highlow_byte_order_raw=None,
            ),
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )

        self.parameter_termination_end_of_pdu._resolve_odxlinks(odxlinks)
        self.parameter_sid._resolve_odxlinks(odxlinks)

        snref_ctx = SnRefContext()
        self.parameter_termination_end_of_pdu._resolve_snrefs(snref_ctx)
        self.parameter_sid._resolve_snrefs(snref_ctx)

    def test_min_max_length_type_end_of_pdu(self) -> None:
        req_param1 = self.parameter_sid
        req_param2 = self.parameter_termination_end_of_pdu
        request = Request(
            odx_id=OdxLinkId("request", doc_frags),
            oid=None,
            short_name="Request",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2]),
        )
        expected_coded_message = bytes([0x12, 0x34])
        expected_param_dict = {"SID": 0x12, "min_max_parameter": bytes([0x34])}

        actual_param_dict = request.decode(expected_coded_message)
        self.assertEqual(dict(actual_param_dict), expected_param_dict)

        actual_coded_message = request.encode(**expected_param_dict)  # type: ignore[arg-type]
        self.assertEqual(actual_coded_message, expected_coded_message)

    def test_min_max_length_type_end_of_pdu_in_structure(self) -> None:
        odxlinks = OdxLinkDatabase()

        struct_param = self.parameter_termination_end_of_pdu

        structure = Structure(
            odx_id=OdxLinkId("structure_id", doc_frags),
            oid=None,
            short_name="Structure_with_End_of_PDU_termination",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([struct_param]),
            byte_size=None,
        )
        odxlinks.update(structure._build_odxlinks())

        req_param1 = self.parameter_sid
        req_param2 = ValueParameter(
            oid=None,
            short_name="min_max_parameter",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(structure.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )

        request = Request(
            odx_id=OdxLinkId("request", doc_frags),
            oid=None,
            short_name="Request",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2]),
        )

        req_param1._resolve_odxlinks(odxlinks)
        req_param2._resolve_odxlinks(odxlinks)
        snref_ctx = SnRefContext()
        req_param1._resolve_snrefs(snref_ctx)
        req_param2._resolve_snrefs(snref_ctx)

        expected_coded_message = bytes([0x12, 0x34])
        expected_param_dict = {
            "SID": 0x12,
            "min_max_parameter": {
                "min_max_parameter": bytes([0x34])
            },
        }

        actual_param_dict = request.decode(expected_coded_message)
        self.assertEqual(dict(actual_param_dict), expected_param_dict)

        actual_coded_message = request.encode(**expected_param_dict)  # type: ignore[arg-type]
        self.assertEqual(actual_coded_message, expected_coded_message)

    def test_physical_constant_parameter(self) -> None:
        odxlinks = OdxLinkDatabase()
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        )
        offset = 0x34
        dop = DataObjectProperty(
            odx_id=OdxLinkId("DOP_ID", doc_frags),
            oid=None,
            short_name="DOP",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(DataType.A_INT32, display_radix=None, precision=None),
            compu_method=LinearCompuMethod(
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
                                numerators=[offset, 1],
                                denominators=[1],
                            ),
                            domain_type=DataType.A_INT32,
                            range_type=DataType.A_INT32),
                    ],
                    prog_code=None,
                    compu_default_value=None),
                compu_phys_to_internal=None,
                internal_type=DataType.A_INT32,
                physical_type=DataType.A_INT32,
            ),
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        odxlinks.update(dop._build_odxlinks())
        req_param1 = CodedConstParameter(
            oid=None,
            short_name="SID",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req_param2 = PhysicalConstantParameter(
            oid=None,
            short_name="physical_constant_parameter",
            long_name=None,
            description=None,
            semantic=None,
            physical_constant_value_raw=f"{offset}",
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        request = Request(
            odx_id=OdxLinkId("request", doc_frags),
            oid=None,
            short_name="Request",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([req_param1, req_param2]),
        )

        req_param1._resolve_odxlinks(odxlinks)
        req_param2._resolve_odxlinks(odxlinks)

        snref_ctx = SnRefContext()
        req_param1._resolve_snrefs(snref_ctx)
        req_param2._resolve_snrefs(snref_ctx)

        expected_coded_message = bytes([0x12, 0x0])
        expected_param_dict = {"SID": 0x12, "physical_constant_parameter": offset}

        actual_param_dict = request.decode(expected_coded_message)
        self.assertEqual(dict(actual_param_dict), expected_param_dict)

        actual_coded_message = request.encode(**expected_param_dict)
        self.assertEqual(actual_coded_message, expected_coded_message)

        self.assertRaises(DecodeError, request.decode, bytes([0x12, 0x34]))


if __name__ == "__main__":
    unittest.main()
