# SPDX-License-Identifier: MIT
import unittest
from xml.etree import ElementTree

from packaging.version import Version

from odxtools.compumethods.compucategory import CompuCategory
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.exceptions import odxrequire
from odxtools.nameditemlist import NamedItemList
from odxtools.odxdoccontext import OdxDocContext
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaldimension import PhysicalDimension
from odxtools.physicaltype import PhysicalType
from odxtools.request import Request
from odxtools.standardlengthtype import StandardLengthType
from odxtools.unit import Unit
from odxtools.unitspec import UnitSpec

doc_frags = (OdxDocFragment("UnitTest", DocType.CONTAINER),)


class TestUnitSpec(unittest.TestCase):

    def test_read_odx(self) -> None:
        expected = UnitSpec(
            physical_dimensions=NamedItemList([
                PhysicalDimension(
                    odx_id=OdxLinkId("ID.metre", doc_frags),
                    short_name="metre",
                    length_exp=1,
                )
            ]),
            units=NamedItemList([
                Unit(
                    odx_id=OdxLinkId("ID.kilometre", doc_frags),
                    short_name="Kilometre",
                    display_name="km",
                    physical_dimension_ref=OdxLinkRef("ID.metre", doc_frags),
                    factor_si_to_unit=1000,
                    offset_si_to_unit=0,
                )
            ]),
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
        spec = UnitSpec.from_et(et_element, OdxDocContext(Version("2.2.0"), doc_frags))
        self.assertEqual(expected.units, spec.units)
        self.assertEqual(expected.physical_dimensions, spec.physical_dimensions)
        self.assertEqual(expected.unit_groups, spec.unit_groups)
        self.assertEqual(expected, spec)

    def test_resolve_odxlinks(self) -> None:
        unit = Unit(
            odx_id=OdxLinkId("unit_time_id", doc_frags),
            short_name="second",
            display_name="s",
            factor_si_to_unit=1,
            offset_si_to_unit=0,
        )
        dct = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop_id", doc_frags),
            short_name="dop_sn",
            diag_coded_type=dct,
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            unit_ref=OdxLinkRef.from_id(unit.odx_id),
        )
        dl_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("BV_id", doc_frags),
            short_name="BaseVariant",
            diag_data_dictionary_spec=DiagDataDictionarySpec(
                data_object_props=NamedItemList([dop]),
                unit_spec=UnitSpec(units=NamedItemList([unit])),
            ),
            requests=NamedItemList([
                Request(
                    odx_id=OdxLinkId("rq_id", doc_frags),
                    short_name="rq_sn",
                    parameters=NamedItemList([
                        CodedConstParameter(
                            short_name="sid",
                            diag_coded_type=dct,
                            coded_value_raw=str(0x12),
                        ),
                        ValueParameter(
                            short_name="time",
                            dop_ref=OdxLinkRef.from_id(dop.odx_id),
                        ),
                    ]),
                )
            ]),
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
