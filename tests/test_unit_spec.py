# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import unittest
from xml.etree import ElementTree

from odxtools.compumethods import IdenticalCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayer import DiagLayer, DiagLayerRaw
from odxtools.diaglayertype import DiagLayerType
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.parameters import CodedConstParameter, ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.structures import Request
from odxtools.units import PhysicalDimension, Unit, UnitSpec
from odxtools.utils import short_name_as_id

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestUnitSpec(unittest.TestCase):

    def test_read_odx(self):
        expected = UnitSpec(
            physical_dimensions=[
                PhysicalDimension(
                    odx_id=OdxLinkId("ID.metre", doc_frags),
                    short_name="metre",
                    length_exp=1,
                    time_exp=0,
                    mass_exp=0,
                    current_exp=0,
                    temperature_exp=0,
                    molar_amount_exp=0,
                    luminous_intensity_exp=0,
                    oid=None,
                    long_name=None,
                    description=None,
                )
            ],
            units=[
                Unit(
                    odx_id=OdxLinkId("ID.kilometre", doc_frags),
                    oid=None,
                    short_name="Kilometre",
                    long_name=None,
                    description=None,
                    display_name="km",
                    physical_dimension_ref=OdxLinkRef("ID.metre", doc_frags),
                    factor_si_to_unit=1000,
                    offset_si_to_unit=0,
                )
            ],
            unit_groups=None,
            sdgs=[],
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
        self.assertEqual(expected.units, spec.units)
        self.assertEqual(expected.physical_dimensions, spec.physical_dimensions)
        self.assertEqual(expected.unit_groups, spec.unit_groups)
        self.assertEqual(expected, spec)

    def test_resolve_odxlinks(self):
        unit = Unit(
            odx_id=OdxLinkId("unit_time_id", doc_frags),
            oid=None,
            short_name="second",
            long_name=None,
            description=None,
            display_name="s",
            physical_dimension_ref=None,
            factor_si_to_unit=1,
            offset_si_to_unit=0,
        )
        dct = StandardLengthType(
            base_data_type="A_UINT32",
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop_id", doc_frags),
            short_name="dop_sn",
            long_name=None,
            description=None,
            is_visible_raw=None,
            diag_coded_type=dct,
            physical_type=PhysicalType("A_UINT32", display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(internal_type="A_UINT32", physical_type="A_UINT32"),
            unit_ref=OdxLinkRef.from_id(unit.odx_id),
            sdgs=[],
        )
        dl_raw = DiagLayerRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("BV_id", doc_frags),
            short_name="BaseVariant",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(short_name_as_id),
            parent_refs=[],
            communication_parameters=[],
            ecu_variant_patterns=[],
            diag_comms=[],
            requests=[
                Request(
                    odx_id=OdxLinkId("rq_id", doc_frags),
                    short_name="rq_sn",
                    long_name=None,
                    description=None,
                    sdgs=[],
                    is_visible_raw=None,
                    parameters=[
                        CodedConstParameter(
                            short_name="sid",
                            long_name=None,
                            description=None,
                            semantic=None,
                            diag_coded_type=dct,
                            coded_value=0x12,
                            byte_position=None,
                            bit_position=None,
                            sdgs=[],
                        ),
                        ValueParameter(
                            short_name="time",
                            long_name=None,
                            description=None,
                            semantic=None,
                            dop_ref=OdxLinkRef.from_id(dop.odx_id),
                            dop_snref=None,
                            physical_default_value_raw=None,
                            byte_position=None,
                            bit_position=None,
                            sdgs=[],
                        ),
                    ],
                    byte_size=None,
                )
            ],
            positive_responses=NamedItemList(short_name_as_id),
            negative_responses=NamedItemList(short_name_as_id),
            global_negative_responses=NamedItemList(short_name_as_id),
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=[dop],
                unit_spec=UnitSpec(
                    units=[unit],
                    physical_dimensions=None,
                    unit_groups=None,
                    sdgs=[],
                ),
                dtc_dops=NamedItemList(short_name_as_id),
                structures=NamedItemList(short_name_as_id),
                end_of_pdu_fields=NamedItemList(short_name_as_id),
                tables=NamedItemList(short_name_as_id),
                env_data_descs=NamedItemList(short_name_as_id),
                env_datas=NamedItemList(short_name_as_id),
                muxs=NamedItemList(short_name_as_id),
                sdgs=[],
            ),
            additional_audiences=NamedItemList(short_name_as_id),
            functional_classes=NamedItemList(short_name_as_id),
            state_charts=NamedItemList(short_name_as_id),
            import_refs=[],
            sdgs=[],
        )
        dl = DiagLayer(diag_layer_raw=dl_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(dl._build_odxlinks())
        dl._resolve_odxlinks(odxlinks)
        dl._finalize_init(odxlinks)

        self.assertEqual(dl.requests[0].parameters[1].dop.unit, unit)


if __name__ == "__main__":
    unittest.main()
