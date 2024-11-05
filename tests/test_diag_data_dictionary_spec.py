# SPDX-License-Identifier: MIT
import unittest
from copy import copy

from examples import somersaultecu
from odxtools.compumethods.compumethod import CompuCategory
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.compumethods.limit import Limit
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.decodestate import DecodeState
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diagnostictroublecode import DiagnosticTroubleCode
from odxtools.dtcdop import DtcDop
from odxtools.encodestate import EncodeState
from odxtools.environmentdata import EnvironmentData
from odxtools.environmentdatadescription import EnvironmentDataDescription
from odxtools.multiplexer import Multiplexer
from odxtools.multiplexercase import MultiplexerCase
from odxtools.multiplexerdefaultcase import MultiplexerDefaultCase
from odxtools.multiplexerswitchkey import MultiplexerSwitchKey
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.physicalconstantparameter import PhysicalConstantParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.standardlengthtype import StandardLengthType
from odxtools.structure import Structure
from odxtools.table import Table
from odxtools.tablerow import TableRow

# the document fragment which is used throughout the test
doc_frags = [OdxDocFragment("DiagDataDictionarySpecTest", "CONTAINER")]


class TestDiagDataDictionarySpec(unittest.TestCase):

    def test_initialization(self) -> None:
        uint8_dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        ident_compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)

        dtc_dop = DtcDop(
            odx_id=OdxLinkId("test_ddds.dop.dtc_dop", doc_frags),
            oid=None,
            short_name="dtc_dop",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=uint8_dct,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            linked_dtc_dops_raw=[],
            compu_method=ident_compu_method,
            dtcs_raw=[
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("test_ddds.dop.dtc_dop.DTC.X10", doc_frags),
                    oid=None,
                    short_name="X10",
                    long_name=None,
                    description=None,
                    trouble_code=0x10,
                    text="Something exploded.",
                    display_trouble_code="X10",
                    level=None,
                    is_temporary_raw=None,
                    sdgs=[],
                )
            ],
            sdgs=[],
            is_visible_raw=None,
        )

        dop_1 = DataObjectProperty(
            odx_id=OdxLinkId("test_ddds.dop.the_dop", doc_frags),
            oid=None,
            short_name="the_dop",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=uint8_dct,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=ident_compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )

        dop_2 = DataObjectProperty(
            odx_id=OdxLinkId("test_ddds.dop.another_dop", doc_frags),
            oid=None,
            short_name="another_dop",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=uint8_dct,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=ident_compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )

        flip_quality_id = OdxLinkId("test_ddds.table.flip_quality", doc_frags)
        flip_quality_ref = OdxLinkRef.from_id(flip_quality_id)
        table = Table(
            odx_id=flip_quality_id,
            oid=None,
            short_name="flip_quality",
            long_name="Flip Quality",
            description=None,
            key_label=None,
            struct_label=None,
            admin_data=None,
            key_dop_ref=None,
            semantic=None,
            table_rows_raw=[
                TableRow(
                    odx_id=OdxLinkId("test_ddds.table.flip_quality.average", doc_frags),
                    oid=None,
                    table_ref=flip_quality_ref,
                    short_name="average",
                    long_name="Average",
                    description=None,
                    semantic=None,
                    dop_ref=None,
                    dop_snref=None,
                    key_raw="3",
                    structure_ref=None,
                    structure_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    odx_id=OdxLinkId("test_ddds.table.flip_quality.good", doc_frags),
                    oid=None,
                    table_ref=flip_quality_ref,
                    short_name="good",
                    long_name="Good",
                    description=None,
                    semantic=None,
                    dop_ref=None,
                    dop_snref=None,
                    key_raw="5",
                    structure_ref=None,
                    structure_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    odx_id=OdxLinkId("test_ddds.table.flip_quality.best", doc_frags),
                    oid=None,
                    table_ref=flip_quality_ref,
                    short_name="best",
                    long_name="Best",
                    description=None,
                    semantic=None,
                    dop_ref=None,
                    dop_snref=None,
                    key_raw="10",
                    structure_ref=None,
                    structure_snref=None,
                    sdgs=[],
                ),
            ],
            sdgs=[],
        )

        env_data = EnvironmentData(
            odx_id=OdxLinkId("test_ddds.env_data.flip_env_data", doc_frags),
            oid=None,
            short_name="flip_env_data",
            long_name="Flip Env Data",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([
                ValueParameter(
                    oid=None,
                    short_name="flip_speed",
                    long_name="Flip Speed",
                    description=None,
                    semantic="DATA",
                    byte_position=0,
                    dop_ref=OdxLinkRef.from_id(dop_1.odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    bit_position=None,
                    sdgs=[],
                ),
                PhysicalConstantParameter(
                    oid=None,
                    short_name="flip_direction",
                    long_name="Flip Direction",
                    description=None,
                    semantic="DATA",
                    byte_position=1,
                    physical_constant_value_raw="1",
                    dop_ref=OdxLinkRef.from_id(dop_1.odx_id),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
            byte_size=None,
            dtc_values=[],
            all_value=None,
        )

        env_data_desc = EnvironmentDataDescription(
            odx_id=OdxLinkId("test_ddds.env_data_desc.flip_env_data_desc", doc_frags),
            oid=None,
            short_name="flip_env_data_desc",
            long_name="Flip Env Data Desc",
            description=None,
            admin_data=None,
            sdgs=[],
            param_snref="flip_speed",
            param_snpathref=None,
            env_datas=NamedItemList(),
            env_data_refs=[OdxLinkRef.from_id(env_data.odx_id)],
        )

        mux_case1_struct = Structure(
            odx_id=OdxLinkId("ddds_test.mux.case1.struct", doc_frags),
            oid=None,
            short_name="mux_case1_struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([
                ValueParameter(
                    oid=None,
                    short_name="min_donation",
                    long_name=None,
                    description=None,
                    semantic=None,
                    dop_ref=OdxLinkRef.from_id(dop_1.odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="min_surface_softness",
                    long_name=None,
                    description=None,
                    semantic=None,
                    dop_ref=OdxLinkRef.from_id(dop_1.odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                )
            ]),
            byte_size=None,
        )

        mux_case2_struct = Structure(
            odx_id=OdxLinkId("ddds_test.mux.case2.struct", doc_frags),
            oid=None,
            short_name="mux_case2_struct",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([
                ValueParameter(
                    oid=None,
                    short_name="min_temperature",
                    long_name=None,
                    description=None,
                    semantic=None,
                    dop_ref=OdxLinkRef.from_id(dop_1.odx_id),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
            byte_size=None,
        )

        mux = Multiplexer(
            odx_id=OdxLinkId("test_ddds.multiplexer.flip_precondition", doc_frags),
            oid=None,
            short_name="flip_precondition",
            long_name="Preconditions for doing flips",
            description=None,
            admin_data=None,
            sdgs=[],
            byte_position=1,
            switch_key=MultiplexerSwitchKey(
                byte_position=0,
                bit_position=0,
                dop_ref=OdxLinkRef.from_id(dop_1.odx_id),
            ),
            default_case=MultiplexerDefaultCase(
                short_name="default_case",
                long_name="Preconditions for Other Actions",
                description=None,
                structure_ref=None,
                structure_snref=None,
            ),
            cases=NamedItemList([
                MultiplexerCase(
                    short_name="forward_flip",
                    long_name="Preconditions for doing a Forward Flip",
                    description=None,
                    lower_limit=Limit(
                        value_raw="1", value_type=DataType.A_INT32, interval_type=None),
                    upper_limit=Limit(
                        value_raw="3", value_type=DataType.A_INT32, interval_type=None),
                    structure_ref=OdxLinkRef.from_id(mux_case1_struct.odx_id),
                    structure_snref=None,
                ),
                MultiplexerCase(
                    short_name="backward_flip",
                    long_name="Preconditions for doing a Backward Flip",
                    description=None,
                    lower_limit=Limit(
                        value_raw="5", value_type=DataType.A_INT32, interval_type=None),
                    upper_limit=Limit(
                        value_raw="10", value_type=DataType.A_INT32, interval_type=None),
                    structure_ref=OdxLinkRef.from_id(mux_case2_struct.odx_id),
                    structure_snref=None,
                ),
            ]),
            is_visible_raw=None,
        )

        ddds = DiagDataDictionarySpec(
            admin_data=None,
            dtc_dops=NamedItemList([dtc_dop]),
            data_object_props=NamedItemList([dop_1, dop_2]),
            tables=NamedItemList([table]),
            env_data_descs=NamedItemList([env_data_desc]),
            env_datas=NamedItemList([env_data]),
            muxs=NamedItemList([mux]),
            structures=NamedItemList([mux_case1_struct, mux_case2_struct]),
            static_fields=NamedItemList(),
            end_of_pdu_fields=NamedItemList(),
            dynamic_length_fields=NamedItemList(),
            dynamic_endmarker_fields=NamedItemList(),
            unit_spec=None,
            sdgs=[],
        )

        # test the short name resolution of TableKeyParameter.
        ecu = somersaultecu.database.ecus.somersault_lazy
        ecu.diag_layer_raw.diag_data_dictionary_spec = ddds
        odxlinks = OdxLinkDatabase()
        odxlinks.update(somersaultecu.database._build_odxlinks())
        odxlinks.update(ecu._build_odxlinks())
        ecu._resolve_odxlinks(odxlinks)
        ecu._finalize_init(database=somersaultecu.database, odxlinks=odxlinks)

        self.assertEqual(ddds.dtc_dops[0], dtc_dop)
        self.assertEqual(ddds.data_object_props[0], dop_1)
        self.assertEqual(ddds.data_object_props.another_dop, dop_2)
        self.assertEqual(ddds.tables[0], table)
        self.assertEqual(ddds.env_data_descs[0], env_data_desc)
        self.assertEqual(ddds.env_datas[0], env_data)
        self.assertEqual(ddds.muxs[0], mux)

        self.assertEqual(len(ddds.structures), 2)
        self.assertEqual(len(ddds.end_of_pdu_fields), 0)

        ddds = ecu.diag_data_dictionary_spec

        # make sure that all locally defined DOPs are present in the finalized ECU
        all_dops = {x.short_name for x in ddds.all_data_object_properties}
        local_dops = {
            "num_flips", "soberness_check", "dizzyness_level", "happiness_level", "duration",
            "temperature", "error_code", "boolean", "uint8", "uint16", "float",
            "flip_env_data_desc", "flip_env_data"
        }
        self.assertEqual(local_dops - all_dops, set())

        # forward flip case
        encode_state = EncodeState(coded_message=bytearray.fromhex("ffee"), cursor_byte_position=2)
        mux.encode_into_pdu(("forward_flip", {
            "min_donation": 3,
            "min_surface_softness": 123
        }), encode_state)
        self.assertEqual(encode_state.coded_message.hex(), "ffee01037b")

        decode_state = DecodeState(
            coded_message=copy(encode_state.coded_message), cursor_byte_position=2)
        decoded = mux.decode_from_pdu(decode_state)
        self.assertEqual(decoded, ("forward_flip", {
            "min_donation": 3,
            "min_surface_softness": 123
        }))

        # backward flip case
        encode_state = EncodeState(coded_message=bytearray.fromhex("ffee"), cursor_byte_position=2)
        mux.encode_into_pdu({7: {"min_temperature": 21}}, encode_state)
        self.assertEqual(encode_state.coded_message.hex(), "ffee0715")

        decode_state = DecodeState(
            coded_message=copy(encode_state.coded_message), cursor_byte_position=2)
        decoded = mux.decode_from_pdu(decode_state)
        self.assertEqual(decoded, ("backward_flip", {"min_temperature": 21}))

        # default case
        encode_state = EncodeState(coded_message=bytearray.fromhex("ffee"), cursor_byte_position=2)
        mux.encode_into_pdu([100, {}], encode_state)
        self.assertEqual(encode_state.coded_message.hex(), "ffee64")

        decode_state = DecodeState(
            coded_message=copy(encode_state.coded_message), cursor_byte_position=2)
        decoded = mux.decode_from_pdu(decode_state)
        self.assertEqual(decoded, ("default_case", {}))


if __name__ == "__main__":
    unittest.main()
