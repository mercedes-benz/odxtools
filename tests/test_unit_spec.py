# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import unittest
from xml.etree import ElementTree

from odxtools.units import read_unit_spec_from_odx, Unit, UnitSpec, PhysicalDimension

from odxtools.compumethods import IdenticalCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diaglayer import DiagLayer
from odxtools.parameters import CodedConstParameter, ValueParameter
from odxtools.structures import Request
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec


class TestUnitSpec(unittest.TestCase):

    def test_read_odx(self):
        expected = UnitSpec(
            physical_dimensions=[
                PhysicalDimension(
                    id="ID.metre",
                    short_name="metre",
                    length_exp=1
                )
            ],
            units=[
                Unit(
                    id="ID.kilometre",
                    short_name="Kilometre",
                    display_name="km",
                    physical_dimension_ref="ID.metre",
                    factor_si_to_unit=.001,
                    offset_si_to_unit=0.
                )
            ]
        )
        # Define an example ECU job as odx
        sample_unit_spec_odx = f"""
            <UNIT-SPEC>
                <UNITS>
                    <UNIT ID="{expected.units[0].id}">
                        <SHORT-NAME>{expected.units[0].short_name}</SHORT-NAME>
                        <DISPLAY-NAME>{expected.units[0].display_name}</DISPLAY-NAME>
                        <FACTOR-SI-TO-UNIT>{expected.units[0].factor_si_to_unit}</FACTOR-SI-TO-UNIT>
                        <OFFSET-SI-TO-UNIT>{expected.units[0].offset_si_to_unit}</OFFSET-SI-TO-UNIT>
                        <PHYSICAL-DIMENSION-REF ID-REF="{expected.units[0].physical_dimension_ref}" />
                    </UNIT>
                </UNITS>
                <PHYSICAL-DIMENSIONS>
                    <PHYSICAL-DIMENSION ID="{expected.physical_dimensions[0].id}">
                        <SHORT-NAME>{expected.physical_dimensions[0].short_name}</SHORT-NAME>
                        <LENGTH-EXP>{expected.physical_dimensions[0].length_exp}</LENGTH-EXP>
                    </PHYSICAL-DIMENSION>
                </PHYSICAL-DIMENSIONS>
            </UNIT-SPEC>
        """
        et_element = ElementTree.fromstring(sample_unit_spec_odx)
        spec = read_unit_spec_from_odx(et_element)
        self.assertEqual(
            expected.units,
            spec.units
        )
        self.assertEqual(
            expected.physical_dimensions,
            spec.physical_dimensions
        )
        self.assertEqual(
            expected.unit_groups,
            spec.unit_groups
        )
        self.assertEqual(
            expected,
            spec
        )

    def test_resolve_references(self):
        unit = Unit(id="unit_time_id", short_name="second", display_name="s")
        dct = StandardLengthType("A_UINT32", 8)
        dop = DataObjectProperty(
            id="dop_id",
            short_name="dop_sn",
            diag_coded_type=dct,
            physical_data_type="A_UINT32",
            compu_method=IdenticalCompuMethod("A_UINT32", "A_UINT32"),
            unit_ref=unit.id
        )
        dl = DiagLayer(
            "BASE-VARIANT",
            id="BV_id",
            short_name="BaseVariant",
            requests=[Request("rq_id", "rq_sn", [
                CodedConstParameter(short_name="sid",
                                    diag_coded_type=dct,
                                    coded_value=0x12),
                ValueParameter("time", dop_ref=dop.id),
            ])],
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=[dop],
                unit_spec=UnitSpec(units=[unit])
            )
        )
        dl.finalize_init()

        self.assertEqual(dl.requests[0].parameters[1].dop.unit, unit)


if __name__ == '__main__':
    unittest.main()
