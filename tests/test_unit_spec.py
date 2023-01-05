# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import unittest
from xml.etree import ElementTree

from odxtools.compumethods import IdenticalCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayer import DiagLayer
from odxtools.diaglayertype import DIAG_LAYER_TYPE
from odxtools.odxlink import OdxDocFragment, OdxLinkId, OdxLinkRef
from odxtools.parameters import CodedConstParameter, ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.structures import Request
from odxtools.units import (PhysicalDimension, Unit, UnitSpec)

doc_frags = [ OdxDocFragment("UnitTest", "WinneThePoh") ]

class TestUnitSpec(unittest.TestCase):

    def test_read_odx(self):
        expected = UnitSpec(
            physical_dimensions=[
                PhysicalDimension(
                    odx_id=OdxLinkId("ID.metre", doc_frags),
                    short_name="metre",
                    length_exp=1
                )
            ],
            units=[
                Unit(
                    odx_id=OdxLinkId("ID.kilometre", doc_frags),
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
                    <UNIT ID="{expected.units[0].odx_id.local_id}">
                        <SHORT-NAME>{expected.units[0].short_name}</SHORT-NAME>
                        <DISPLAY-NAME>{expected.units[0].display_name}</DISPLAY-NAME>
                        <FACTOR-SI-TO-UNIT>{expected.units[0].factor_si_to_unit}</FACTOR-SI-TO-UNIT>
                        <OFFSET-SI-TO-UNIT>{expected.units[0].offset_si_to_unit}</OFFSET-SI-TO-UNIT>
                        <PHYSICAL-DIMENSION-REF ID-REF="{expected.units[0].physical_dimension_ref.ref_id}" />
                    </UNIT>
                </UNITS>
                <PHYSICAL-DIMENSIONS>
                    <PHYSICAL-DIMENSION ID="{expected.physical_dimensions[0].odx_id.local_id}">
                        <SHORT-NAME>{expected.physical_dimensions[0].short_name}</SHORT-NAME>
                        <LENGTH-EXP>{expected.physical_dimensions[0].length_exp}</LENGTH-EXP>
                    </PHYSICAL-DIMENSION>
                </PHYSICAL-DIMENSIONS>
            </UNIT-SPEC>
        """
        et_element = ElementTree.fromstring(sample_unit_spec_odx)
        spec = UnitSpec.from_et(et_element, doc_frags)
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
        unit = Unit(odx_id=OdxLinkId("unit_time_id", doc_frags),
                    short_name="second",
                    display_name="s")
        dct = StandardLengthType(base_data_type="A_UINT32", bit_length=8)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop_id", doc_frags),
            short_name="dop_sn",
            diag_coded_type=dct,
            physical_type=PhysicalType("A_UINT32"),
            compu_method=IdenticalCompuMethod(internal_type="A_UINT32",
                                              physical_type="A_UINT32"),
            unit_ref=OdxLinkRef.from_id(unit.odx_id)
        )
        dl = DiagLayer(
            variant_type=DIAG_LAYER_TYPE.BASE_VARIANT,
            odx_id=OdxLinkId("BV_id", doc_frags),
            short_name="BaseVariant",
            requests=[Request(odx_id=OdxLinkId("rq_id", doc_frags),
                              short_name="rq_sn",
                              parameters=[
                                  CodedConstParameter(short_name="sid",
                                                      diag_coded_type=dct,
                                                      coded_value=0x12),
                                  ValueParameter(short_name="time",
                                                 dop_ref=OdxLinkRef.from_id(dop.odx_id)),
                              ])],
            diag_data_dictionary_spec=DiagDataDictionarySpec(data_object_props=[dop],
                                                             unit_spec=UnitSpec(units=[unit])
                                                             )
        )
        dl.finalize_init()

        self.assertEqual(dl.requests[0].parameters[1].dop.unit, unit)


if __name__ == '__main__':
    unittest.main()
