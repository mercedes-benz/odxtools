# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest

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

        ddds = DiagDataDictionarySpec(dtc_dops=[dtc_dop],
                                      data_object_props=[dop_1, dop_2],
                                      tables=[table])

        self.assertEqual(ddds.dtc_dops[0], dtc_dop)
        self.assertEqual(ddds.data_object_props[0], dop_1)
        self.assertEqual(ddds.data_object_props.another_dop, dop_2)
        self.assertEqual(ddds.tables[0], table)

        self.assertEqual(len(ddds.structures), 0)
        self.assertEqual(len(ddds.end_of_pdu_fields), 0)

        self.assertEqual(set(ddds.all_data_object_properties),
                         set([dtc_dop, dop_1, dop_2, table]))


if __name__ == '__main__':
    unittest.main()
