# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest

from odxtools.envdatadesc import EnvironmentDataDescription
from odxtools.multiplexer import Multiplexer, MultiplexerSwitchKey, MultiplexerDefaultCase, MultiplexerCase

from odxtools import ValueParameter, PhysicalConstantParameter

from odxtools.envdata import EnvironmentData
from odxtools.table import Table, TableRow

from odxtools.compumethods import IdenticalCompuMethod
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.dataobjectproperty import DataObjectProperty, DiagnosticTroubleCode, DtcDop
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.physicaltype import PhysicalType


class TestDiagDataDictionarySpec(unittest.TestCase):
    def test_initialization(self):
        uint_type = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        ident_compu_method = IdenticalCompuMethod("A_UINT32", "A_UINT32")

        dtc_dop = DtcDop("DOP.dtc_dop", "dtc_dop",
                         diag_coded_type=uint_type,
                         physical_type=PhysicalType("A_UINT32"),
                         compu_method=ident_compu_method,
                         dtcs=[DiagnosticTroubleCode(
                             "DOP.dtc_dop.DTC.X10",
                             "X10",
                             0x10,
                             "Something exploded.",
                             display_trouble_code="X10"
                         )])

        dop_1 = DataObjectProperty("DOP.the_dop",
                                   "the_dop",
                                   diag_coded_type=uint_type,
                                   physical_type=PhysicalType("A_UINT32"),
                                   compu_method=ident_compu_method)

        dop_2 = DataObjectProperty("DOP.another_dop",
                                   "another_dop",
                                   diag_coded_type=uint_type,
                                   physical_type=PhysicalType("A_UINT32"),
                                   compu_method=ident_compu_method)

        table = Table(
                id="somersault.table.flip_quality",
                short_name="flip_quality",
                long_name="Flip Quality",
                key_dop_ref="",
                table_rows=[
                    TableRow(
                        id="somersault.table.flip_quality.average",
                        short_name="average",
                        long_name="Average",
                        key=3,
                        structure_ref="",
                    ),
                    TableRow(
                        id="somersault.table.flip_quality.good",
                        short_name="good",
                        long_name="Good",
                        key=5,
                        structure_ref="",
                    ),
                    TableRow(
                        id="somersault.table.flip_quality.best",
                        short_name="best",
                        long_name="Best",
                        key=10,
                        structure_ref="",
                    ),
                ]
            )

        env_data = EnvironmentData(
            id="somersault.env_data.flip_env_data",
            short_name="flip_env_data",
            long_name="Flip Env Data",
            parameters=[
                ValueParameter(
                    short_name="flip_speed",
                    long_name="Flip Speed",
                    byte_position=0,
                    semantic="DATA",
                    dop_ref="dop-ref",
                ),
                PhysicalConstantParameter(
                    short_name="flip_direction",
                    long_name="Flip Direction",
                    byte_position=1,
                    semantic="DATA",
                    physical_constant_value=1,
                    dop_ref="dop-ref",
                ),
            ]
        )

        env_data_desc = EnvironmentDataDescription(
            id="somersault.env_data_desc.flip_env_data_desc",
            short_name="flip_env_data_desc",
            long_name="Flip Env Data Desc",
            param_snref="flip_speed",
            env_data_refs=["somersault.env_data.flip_env_data"],
        )

        mux = Multiplexer(
            id="somersault.multiplexer.flip_preference",
            short_name="flip_preference",
            long_name="Flip Preference",
            byte_position=0,
            switch_key=MultiplexerSwitchKey(
                byte_position=0,
                bit_position=0,
                dop_ref="dop-ref",
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
                )
            ]
        )

        ddds = DiagDataDictionarySpec(dtc_dops=[dtc_dop],
                                      data_object_props=[dop_1, dop_2],
                                      tables=[table],
                                      env_data_descs=[env_data_desc],
                                      env_datas=[env_data],
                                      muxs=[mux])

        self.assertEqual(ddds.dtc_dops[0], dtc_dop)
        self.assertEqual(ddds.data_object_props[0], dop_1)
        self.assertEqual(ddds.data_object_props.another_dop, dop_2)
        self.assertEqual(ddds.tables[0], table)
        self.assertEqual(ddds.env_data_descs[0], env_data_desc)
        self.assertEqual(ddds.env_datas[0], env_data)
        self.assertEqual(ddds.muxs[0], mux)

        self.assertEqual(len(ddds.structures), 0)
        self.assertEqual(len(ddds.end_of_pdu_fields), 0)

        self.assertEqual(set(ddds.all_data_object_properties),
                         set([dtc_dop, dop_1, dop_2, table]))


if __name__ == '__main__':
    unittest.main()
