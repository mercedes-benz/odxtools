# SPDX-License-Identifier: MIT
import unittest
from xml.etree import ElementTree

from odxtools.compumethods.compumethod import CompuCategory
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.exceptions import odxrequire
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaldimension import PhysicalDimension
from odxtools.physicaltype import PhysicalType
from odxtools.request import Request
from odxtools.standardlengthtype import StandardLengthType
from odxtools.unit import Unit
from odxtools.unitspec import UnitSpec

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestUnitSpec(unittest.TestCase):

    def test_read_odx(self) -> None:
        expected = UnitSpec(
            physical_dimensions=NamedItemList([
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
            ]),
            units=NamedItemList([
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
            ]),
            unit_groups=NamedItemList(),
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
                        <PHYSICAL-DIMENSION-REF ID-REF="{odxrequire(expected.units[0].physical_dimension_ref).ref_id}" />
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

    def test_resolve_odxlinks(self) -> None:
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
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop_id", doc_frags),
            oid=None,
            short_name="dop_sn",
            admin_data=None,
            long_name=None,
            description=None,
            diag_coded_type=dct,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            unit_ref=OdxLinkRef.from_id(unit.odx_id),
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        dl_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("BV_id", doc_frags),
            oid=None,
            short_name="BaseVariant",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(),
            functional_classes=NamedItemList(),
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                admin_data=None,
                data_object_props=NamedItemList([dop]),
                unit_spec=UnitSpec(
                    units=NamedItemList([unit]),
                    physical_dimensions=NamedItemList(),
                    unit_groups=NamedItemList(),
                    sdgs=[],
                ),
                dtc_dops=NamedItemList(),
                structures=NamedItemList(),
                end_of_pdu_fields=NamedItemList(),
                dynamic_length_fields=NamedItemList(),
                dynamic_endmarker_fields=NamedItemList(),
                static_fields=NamedItemList(),
                tables=NamedItemList(),
                env_data_descs=NamedItemList(),
                env_datas=NamedItemList(),
                muxs=NamedItemList(),
                sdgs=[],
            ),
            diag_comms_raw=[],
            requests=NamedItemList([
                Request(
                    odx_id=OdxLinkId("rq_id", doc_frags),
                    oid=None,
                    short_name="rq_sn",
                    admin_data=None,
                    long_name=None,
                    description=None,
                    sdgs=[],
                    parameters=NamedItemList([
                        CodedConstParameter(
                            oid=None,
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
                            oid=None,
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
                    ]),
                )
            ]),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
            global_negative_responses=NamedItemList(),
            import_refs=[],
            state_charts=NamedItemList(),
            additional_audiences=NamedItemList(),
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
        dl = EcuVariant(diag_layer_raw=dl_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(dl._build_odxlinks())
        db = Database()
        dl._resolve_odxlinks(odxlinks)
        dl._finalize_init(db, odxlinks)

        param = dl.requests[0].parameters[1]
        assert isinstance(param, ValueParameter)
        _dop = param.dop
        assert isinstance(_dop, DataObjectProperty)
        self.assertEqual(_dop.unit, unit)


if __name__ == "__main__":
    unittest.main()
