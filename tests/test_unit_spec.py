# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest
from xml.etree import ElementTree
from odxtools.physicaltype import PhysicalType

from odxtools.units import read_unit_spec_from_odx, Unit, UnitSpec, PhysicalDimension

from odxtools.compumethods import IdenticalCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diaglayer import DiagLayer
from odxtools.parameters import CodedConstParameter, ValueParameter
from odxtools.structures import Request
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.odxlink import OdxLinkId, OdxLinkRef, OdxDocFragment

doc_frags = [ OdxDocFragment("UnitTest", "WinneThePoh") ]

class TestUnitSpec(unittest.TestCase):

    def test_read_odx(self):
        expected = UnitSpec(
            physical_dimensions=[
                PhysicalDimension(
                    odx_link_id=OdxLinkId("ID.metre", doc_frags),
                    short_name="metre",
                    length_exp=1
                )
            ],
            units=[
                Unit(
                    odx_link_id=OdxLinkId("ID.kilometre", doc_frags),
                    short_name="Kilometre",
                    display_name="km",
                    physical_dimension_ref=OdxLinkRef("ID.metre", doc_frags),
                    factor_si_to_unit=1000,
                    offset_si_to_unit=0
                )
            ]
        )
        # Define an example ECU job as odx
        sample_unit_spec_odx = f"""
            <UNIT-SPEC>
                <UNITS>
                    <UNIT ID="{expected.units[0].odx_link_id.local_id}">
                        <SHORT-NAME>{expected.units[0].short_name}</SHORT-NAME>
                        <DISPLAY-NAME>{expected.units[0].display_name}</DISPLAY-NAME>
                        <FACTOR-SI-TO-UNIT>{expected.units[0].factor_si_to_unit}</FACTOR-SI-TO-UNIT>
                        <OFFSET-SI-TO-UNIT>{expected.units[0].offset_si_to_unit}</OFFSET-SI-TO-UNIT>
                        <PHYSICAL-DIMENSION-REF ID-REF="{expected.units[0].physical_dimension_ref.ref_id}" />
                    </UNIT>
                </UNITS>
                <PHYSICAL-DIMENSIONS>
                    <PHYSICAL-DIMENSION ID="{expected.physical_dimensions[0].odx_link_id.local_id}">
                        <SHORT-NAME>{expected.physical_dimensions[0].short_name}</SHORT-NAME>
                        <LENGTH-EXP>{expected.physical_dimensions[0].length_exp}</LENGTH-EXP>
                    </PHYSICAL-DIMENSION>
                </PHYSICAL-DIMENSIONS>
            </UNIT-SPEC>
        """
        et_element = ElementTree.fromstring(sample_unit_spec_odx)
        spec = read_unit_spec_from_odx(et_element, doc_frags=doc_frags)
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
        unit = Unit(odx_link_id=OdxLinkId("unit_time_id", doc_frags),
                    short_name="second",
                    display_name="s")
        dct = StandardLengthType("A_UINT32", 8)
        dop = DataObjectProperty(
            odx_link_id=OdxLinkId("dop_id", doc_frags),
            short_name="dop_sn",
            diag_coded_type=dct,
            physical_type=PhysicalType("A_UINT32"),
            compu_method=IdenticalCompuMethod("A_UINT32", "A_UINT32"),
            unit_ref=OdxLinkRef.from_id(unit.odx_link_id)
        )
        dl = DiagLayer(
            "BASE-VARIANT",
            odx_link_id=OdxLinkId("BV_id", doc_frags),
            short_name="BaseVariant",
            requests=[Request(OdxLinkId("rq_id", doc_frags), "rq_sn", [
                CodedConstParameter(short_name="sid",
                                    diag_coded_type=dct,
                                    coded_value=0x12),
                ValueParameter("time", dop_ref=OdxLinkRef.from_id(dop.odx_link_id)),
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
