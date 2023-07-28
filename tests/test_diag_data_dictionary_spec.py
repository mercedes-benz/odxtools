# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import unittest

from examples import somersaultecu
from odxtools import PhysicalConstantParameter, TableKeyParameter, ValueParameter
from odxtools.compumethods import IdenticalCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty, DiagnosticTroubleCode, DtcDop
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.envdata import EnvironmentData
from odxtools.envdatadesc import EnvironmentDataDescription
from odxtools.multiplexer import (Multiplexer, MultiplexerCase, MultiplexerDefaultCase,
                                  MultiplexerSwitchKey)
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.physicaltype import PhysicalType
from odxtools.table import Table, TableRow
from odxtools.utils import short_name_as_id

# the document fragment which is used throughout the test
doc_frags = [OdxDocFragment("UnitTest", "unit_test_doc")]


class TestDiagDataDictionarySpec(unittest.TestCase):

    def test_initialization(self):
        uint_type = StandardLengthType(
            base_data_type="A_UINT32",
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        ident_compu_method = IdenticalCompuMethod(
            internal_type="A_UINT32", physical_type="A_UINT32")

        dtc_dop = DtcDop(
            odx_id=OdxLinkId("DOP.dtc_dop", doc_frags),
            short_name="dtc_dop",
            long_name=None,
            description=None,
            is_visible_raw=None,
            diag_coded_type=uint_type,
            physical_type=PhysicalType("A_UINT32", display_radix=None, precision=None),
            linked_dtc_dop_refs=[],
            compu_method=ident_compu_method,
            unit_ref=None,
            dtcs_raw=[
                DiagnosticTroubleCode(
                    odx_id=OdxLinkId("DOP.dtc_dop.DTC.X10", doc_frags),
                    short_name="X10",
                    trouble_code=0x10,
                    text="Something exploded.",
                    display_trouble_code="X10",
                    level=None,
                    is_temporary_raw=None,
                    sdgs=[],
                )
            ],
            sdgs=[],
        )

        dop_1 = DataObjectProperty(
            odx_id=OdxLinkId("DOP.the_dop", doc_frags),
            short_name="the_dop",
            long_name=None,
            description=None,
            is_visible_raw=None,
            diag_coded_type=uint_type,
            physical_type=PhysicalType("A_UINT32", display_radix=None, precision=None),
            compu_method=ident_compu_method,
            unit_ref=None,
            sdgs=[],
        )

        dop_2 = DataObjectProperty(
            odx_id=OdxLinkId("DOP.another_dop", doc_frags),
            short_name="another_dop",
            long_name=None,
            description=None,
            is_visible_raw=None,
            diag_coded_type=uint_type,
            physical_type=PhysicalType("A_UINT32", display_radix=None, precision=None),
            compu_method=ident_compu_method,
            unit_ref=None,
            sdgs=[],
        )

        flip_quality_id = OdxLinkId("somersault.table.flip_quality", doc_frags)
        flip_quality_ref = OdxLinkRef.from_id(flip_quality_id)
        table = Table(
            odx_id=flip_quality_id,
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
                    odx_id=OdxLinkId("somersault.table.flip_quality.average", doc_frags),
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
                    odx_id=OdxLinkId("somersault.table.flip_quality.good", doc_frags),
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
                    odx_id=OdxLinkId("somersault.table.flip_quality.best", doc_frags),
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
            odx_id=OdxLinkId("somersault.env_data.flip_env_data", doc_frags),
            short_name="flip_env_data",
            long_name="Flip Env Data",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                ValueParameter(
                    short_name="flip_speed",
                    long_name="Flip Speed",
                    description=None,
                    semantic="DATA",
                    byte_position=0,
                    dop_ref=OdxLinkRef("somersault.DOP.float", doc_frags),
                    dop_snref=None,
                    physical_default_value_raw=None,
                    bit_position=None,
                    sdgs=[],
                ),
                PhysicalConstantParameter(
                    short_name="flip_direction",
                    long_name="Flip Direction",
                    description=None,
                    semantic="DATA",
                    byte_position=1,
                    physical_constant_value=1,
                    dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
                TableKeyParameter(
                    short_name="flip_quality",
                    long_name=None,
                    description=None,
                    sdgs=[],
                    semantic="DATA",
                    byte_position=2,
                    bit_position=None,
                    odx_id=OdxLinkId("somersault.env_data.flip_quality", doc_frags),
                    table_ref=None,
                    table_row_ref=None,
                    table_snref="flip_quality",  # cf. somersaultecu
                    table_row_snref="good",
                ),
            ],
            byte_size=None,
            dtc_values=[],
        )

        env_data_desc = EnvironmentDataDescription(
            odx_id=OdxLinkId("somersault.env_data_desc.flip_env_data_desc", doc_frags),
            short_name="flip_env_data_desc",
            long_name="Flip Env Data Desc",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            param_snref="flip_speed",
            param_snpathref=None,
            env_datas=[],
            env_data_refs=[OdxLinkRef.from_id(env_data.odx_id)],
        )

        mux = Multiplexer(
            odx_id=OdxLinkId("somersault.multiplexer.flip_preference", doc_frags),
            short_name="flip_preference",
            long_name="Flip Preference",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            byte_position=0,
            switch_key=MultiplexerSwitchKey(
                byte_position=0,
                bit_position=0,
                dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
            ),
            default_case=MultiplexerDefaultCase(
                short_name="default_case",
                long_name="Default Case",
                structure_ref="structure_ref",
            ),
            cases=[
                MultiplexerCase(
                    short_name="forward_flip",
                    long_name="Forward Flip",
                    lower_limit="1",
                    upper_limit="3",
                    structure_ref="structure_ref",
                ),
                MultiplexerCase(
                    short_name="backward_flip",
                    long_name="Backward Flip",
                    lower_limit="1",
                    upper_limit="3",
                    structure_ref="structure_ref",
                ),
            ],
        )

        ddds = DiagDataDictionarySpec(
            dtc_dops=[dtc_dop],
            data_object_props=NamedItemList(short_name_as_id, [dop_1, dop_2]),
            tables=NamedItemList(short_name_as_id, [table]),
            env_data_descs=NamedItemList(short_name_as_id, [env_data_desc]),
            env_datas=NamedItemList(short_name_as_id, [env_data]),
            muxs=NamedItemList(short_name_as_id, [mux]),
            structures=NamedItemList(short_name_as_id),
            end_of_pdu_fields=NamedItemList(short_name_as_id),
            unit_spec=None,
            sdgs=[],
        )

        # test the short name resolution of TableKeyParameter.
        odxlinks = OdxLinkDatabase()
        ecu = somersaultecu.database.ecus.somersault_lazy
        ecu.diag_layer_raw.diag_data_dictionary_spec = ddds
        odxlinks.update(ecu._build_odxlinks())
        table._resolve_odxlinks(odxlinks)

        self.assertEqual(ddds.dtc_dops[0], dtc_dop)
        self.assertEqual(ddds.data_object_props[0], dop_1)
        self.assertEqual(ddds.data_object_props.another_dop, dop_2)
        self.assertEqual(ddds.tables[0], table)
        self.assertEqual(ddds.env_data_descs[0], env_data_desc)
        self.assertEqual(ddds.env_datas[0], env_data)
        self.assertEqual(ddds.muxs[0], mux)

        self.assertEqual(len(ddds.structures), 0)
        self.assertEqual(len(ddds.end_of_pdu_fields), 0)

        self.assertEqual({x.short_name
                          for x in ddds.all_data_object_properties},
                         {x.short_name
                          for x in (dtc_dop, dop_1, dop_2, table)})


if __name__ == "__main__":
    unittest.main()
