# SPDX-License-Identifier: MIT
import inspect
import os
import unittest
from io import BytesIO
from typing import NamedTuple, cast
from xml.etree import ElementTree

import jinja2

import odxtools
from odxtools.additionalaudience import AdditionalAudience
from odxtools.audience import Audience
from odxtools.compumethods.compuconst import CompuConst
from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuCategory
from odxtools.compumethods.compurationalcoeffs import CompuRationalCoeffs
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.limit import Limit
from odxtools.compumethods.linearcompumethod import LinearCompuMethod
from odxtools.compumethods.texttablecompumethod import TexttableCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.description import Description
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.exceptions import odxrequire
from odxtools.functionalclass import FunctionalClass
from odxtools.inputparam import InputParam
from odxtools.library import Library
from odxtools.nameditemlist import NamedItemList
from odxtools.negoutputparam import NegOutputParam
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.outputparam import OutputParam
from odxtools.physicaltype import PhysicalType
from odxtools.progcode import ProgCode
from odxtools.singleecujob import SingleEcuJob
from odxtools.standardlengthtype import StandardLengthType
from odxtools.writepdxfile import jinja2_odxraise_helper, make_bool_xml_attrib, make_xml_attrib

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestSingleEcuJob(unittest.TestCase):

    def setUp(self) -> None:
        """Create three objects:

        * self.singleecujob_object: SingleEcuJob - job to be tested
        * self.context: NamedTuple - elements referenced by the SingleEcuJob
        * self.singleecujob_odx: string - odx description of self.singleecujob_object
        """
        super().setUp()

        class Context(NamedTuple):
            """odx elements referenced by the tested single ECU job, i.e., elements needed in the `odxlinks` when resolving references"""

            extensiveTask: FunctionalClass
            specialAudience: AdditionalAudience
            inputDOP: DataObjectProperty
            outputDOP: DataObjectProperty
            negOutputDOP: DataObjectProperty

        self.context = Context(
            extensiveTask=FunctionalClass(
                odx_id=OdxLinkId("ID.extensiveTask", doc_frags),
                oid=None,
                short_name="extensiveTask",
                long_name=None,
                description=None,
            ),
            specialAudience=AdditionalAudience(
                odx_id=OdxLinkId("ID.specialAudience", doc_frags),
                oid=None,
                short_name="specialAudience",
                long_name=None,
                description=None,
            ),
            inputDOP=DataObjectProperty(
                odx_id=OdxLinkId("ID.inputDOP", doc_frags),
                oid=None,
                short_name="inputDOP",
                long_name=None,
                description=None,
                admin_data=None,
                diag_coded_type=StandardLengthType(
                    base_data_type=DataType.A_INT32,
                    bit_length=1,
                    bit_mask=None,
                    base_type_encoding=None,
                    is_condensed_raw=None,
                    is_highlow_byte_order_raw=None,
                ),
                physical_type=PhysicalType(
                    DataType.A_UNICODE2STRING, display_radix=None, precision=None),
                compu_method=TexttableCompuMethod(
                    category=CompuCategory.TEXTTABLE,
                    compu_phys_to_internal=None,
                    physical_type=DataType.A_UNICODE2STRING,
                    compu_internal_to_phys=CompuInternalToPhys(
                        compu_scales=[
                            CompuScale(
                                "yes",
                                lower_limit=Limit(
                                    value_raw="0", value_type=DataType.A_INT32, interval_type=None),
                                compu_const=CompuConst(
                                    v=None, vt="Yes!", data_type=DataType.A_UTF8STRING),
                                description=None,
                                compu_inverse_value=None,
                                upper_limit=None,
                                compu_rational_coeffs=None,
                                domain_type=DataType.A_INT32,
                                range_type=DataType.A_UNICODE2STRING,
                            ),
                            CompuScale(
                                "no",
                                lower_limit=Limit(
                                    value_raw="1", value_type=DataType.A_INT32, interval_type=None),
                                compu_const=CompuConst(
                                    v=None, vt="No!", data_type=DataType.A_UTF8STRING),
                                description=None,
                                compu_inverse_value=None,
                                upper_limit=None,
                                compu_rational_coeffs=None,
                                domain_type=DataType.A_INT32,
                                range_type=DataType.A_UNICODE2STRING),
                        ],
                        prog_code=None,
                        compu_default_value=None,
                    ),
                    internal_type=DataType.A_UINT32,
                ),
                unit_ref=None,
                sdgs=[],
                internal_constr=None,
                physical_constr=None,
            ),
            outputDOP=DataObjectProperty(
                odx_id=OdxLinkId("ID.outputDOP", doc_frags),
                oid=None,
                short_name="outputDOP",
                long_name=None,
                description=None,
                admin_data=None,
                diag_coded_type=StandardLengthType(
                    base_data_type=DataType.A_INT32,
                    bit_length=1,
                    bit_mask=None,
                    base_type_encoding=None,
                    is_condensed_raw=None,
                    is_highlow_byte_order_raw=None,
                ),
                physical_type=PhysicalType(
                    DataType.A_UNICODE2STRING, display_radix=None, precision=None),
                compu_method=LinearCompuMethod(
                    category=CompuCategory.LINEAR,
                    compu_internal_to_phys=CompuInternalToPhys(
                        compu_scales=[
                            CompuScale(
                                short_label=None,
                                description=None,
                                lower_limit=None,
                                upper_limit=None,
                                compu_inverse_value=None,
                                compu_const=None,
                                compu_rational_coeffs=CompuRationalCoeffs(
                                    value_type=DataType.A_INT32,
                                    numerators=[1, -1],
                                    denominators=[1],
                                ),
                                domain_type=DataType.A_INT32,
                                range_type=DataType.A_INT32),
                        ],
                        prog_code=None,
                        compu_default_value=None),
                    compu_phys_to_internal=None,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32),
                unit_ref=None,
                sdgs=[],
                internal_constr=None,
                physical_constr=None,
            ),
            negOutputDOP=DataObjectProperty(
                odx_id=OdxLinkId("ID.negOutputDOP", doc_frags),
                oid=None,
                short_name="negOutputDOP",
                long_name=None,
                description=None,
                admin_data=None,
                diag_coded_type=StandardLengthType(
                    base_data_type=DataType.A_INT32,
                    bit_length=1,
                    bit_mask=None,
                    base_type_encoding=None,
                    is_condensed_raw=None,
                    is_highlow_byte_order_raw=None,
                ),
                physical_type=PhysicalType(
                    DataType.A_UNICODE2STRING, display_radix=None, precision=None),
                compu_method=LinearCompuMethod(
                    category=CompuCategory.LINEAR,
                    compu_internal_to_phys=CompuInternalToPhys(
                        compu_scales=[
                            CompuScale(
                                short_label=None,
                                description=None,
                                lower_limit=None,
                                upper_limit=None,
                                compu_inverse_value=None,
                                compu_const=None,
                                compu_rational_coeffs=CompuRationalCoeffs(
                                    value_type=DataType.A_INT32,
                                    numerators=[1, -1],
                                    denominators=[1],
                                ),
                                domain_type=DataType.A_INT32,
                                range_type=DataType.A_INT32),
                        ],
                        prog_code=None,
                        compu_default_value=None),
                    compu_phys_to_internal=None,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32,
                ),
                unit_ref=None,
                sdgs=[],
                internal_constr=None,
                physical_constr=None,
            ),
        )

        input_params = NamedItemList([
            InputParam(
                oid=None,
                short_name="inputParam",
                long_name=None,
                description=None,
                semantic=None,
                physical_default_value="Yes!",
                dop_base_ref=OdxLinkRef.from_id(self.context.inputDOP.odx_id),
            )
        ])
        output_params = NamedItemList([
            OutputParam(
                odx_id=OdxLinkId("ID.outputParam", doc_frags),
                oid=None,
                semantic="DATA",
                short_name="outputParam",
                long_name="The Output Param",
                description=Description.from_string("<p>The one and only output of this job.</p>"),
                dop_base_ref=OdxLinkRef.from_id(self.context.outputDOP.odx_id),
            )
        ])
        neg_output_params = NamedItemList([
            NegOutputParam(
                short_name="NegativeOutputParam",
                long_name=None,
                description=Description.from_string("<p>The one and only output of this job.</p>"),
                dop_base_ref=OdxLinkRef.from_id(self.context.negOutputDOP.odx_id),
            )
        ])

        self.singleecujob_object = SingleEcuJob(
            odx_id=OdxLinkId("ID.JumpStart", doc_frags),
            oid=None,
            short_name="JumpStart",
            long_name=None,
            description=None,
            admin_data=None,
            semantic=None,
            functional_class_refs=[OdxLinkRef.from_id(self.context.extensiveTask.odx_id)],
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            diagnostic_class=None,
            audience=Audience(
                enabled_audience_refs=[OdxLinkRef.from_id(self.context.specialAudience.odx_id)],
                disabled_audience_refs=[],
                is_supplier_raw=None,
                is_development_raw=None,
                is_aftersales_raw=None,
                is_aftermarket_raw=None,
                is_manufacturing_raw=False,
            ),
            prog_codes=[
                ProgCode(
                    code_file="abc.jar",
                    encryption="RSA512",
                    syntax="JAR",
                    revision="0.12.34",
                    entrypoint="CalledClass",
                    library_refs=[OdxLinkRef("my.favourite.lib", doc_frags)],
                )
            ],
            input_params=input_params,
            output_params=output_params,
            neg_output_params=neg_output_params,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            sdgs=[],
        )

        self.singleecujob_odx = f"""
            <SINGLE-ECU-JOB ID="{self.singleecujob_object.odx_id.local_id}">
                <SHORT-NAME>{self.singleecujob_object.short_name}</SHORT-NAME>
                <FUNCT-CLASS-REFS>
                    <FUNCT-CLASS-REF ID-REF="{self.singleecujob_object.functional_class_refs[0].ref_id}"/>
                </FUNCT-CLASS-REFS>
                <AUDIENCE IS-MANUFACTURING="false">
                    <ENABLED-AUDIENCE-REFS>
                        <ENABLED-AUDIENCE-REF ID-REF="{cast(Audience, self.singleecujob_object.audience).enabled_audience_refs[0].ref_id}"/>
                    </ENABLED-AUDIENCE-REFS>
                </AUDIENCE>
                <PROG-CODES>
                    <PROG-CODE>
                        <CODE-FILE>{self.singleecujob_object.prog_codes[0].code_file}</CODE-FILE>
                        <ENCRYPTION>{self.singleecujob_object.prog_codes[0].encryption}</ENCRYPTION>
                        <SYNTAX>{self.singleecujob_object.prog_codes[0].syntax}</SYNTAX>
                        <REVISION>{self.singleecujob_object.prog_codes[0].revision}</REVISION>
                        <ENTRYPOINT>{self.singleecujob_object.prog_codes[0].entrypoint}</ENTRYPOINT>
                        <LIBRARY-REFS>
                            <LIBRARY-REF ID-REF="{self.singleecujob_object.prog_codes[0].library_refs[0].ref_id}"/>
                        </LIBRARY-REFS>
                    </PROG-CODE>
                </PROG-CODES>
                <INPUT-PARAMS>
                    <INPUT-PARAM>
                        <SHORT-NAME>{input_params[0].short_name}</SHORT-NAME>
                        <PHYSICAL-DEFAULT-VALUE>{input_params[0].physical_default_value}</PHYSICAL-DEFAULT-VALUE>
                        <DOP-BASE-REF ID-REF="{input_params[0].dop_base_ref.ref_id}"/>
                    </INPUT-PARAM>
                </INPUT-PARAMS>
                <OUTPUT-PARAMS>
                    <OUTPUT-PARAM ID="{output_params[0].odx_id.local_id}" SEMANTIC="{output_params[0].semantic}">
                        <SHORT-NAME>{output_params[0].short_name}</SHORT-NAME>
                        <LONG-NAME>{output_params[0].long_name}</LONG-NAME>
                        <DESC>{output_params[0].description}</DESC>
                        <DOP-BASE-REF ID-REF="{output_params[0].dop_base_ref.ref_id}"/>
                    </OUTPUT-PARAM>
                </OUTPUT-PARAMS>
                <NEG-OUTPUT-PARAMS>
                    <NEG-OUTPUT-PARAM>
                        <SHORT-NAME>{neg_output_params[0].short_name}</SHORT-NAME>
                        <DESC>{neg_output_params[0].description}</DESC>
                        <DOP-BASE-REF ID-REF="{neg_output_params[0].dop_base_ref.ref_id}"/>
                    </NEG-OUTPUT-PARAM>
                </NEG-OUTPUT-PARAMS>
            </SINGLE-ECU-JOB>
        """

    def test_read_odx(self) -> None:
        expected = self.singleecujob_object
        sample_single_ecu_job_odx = self.singleecujob_odx
        et_element = ElementTree.fromstring(sample_single_ecu_job_odx)
        sej = SingleEcuJob.from_et(et_element, doc_frags)
        self.assertEqual(expected.prog_codes, sej.prog_codes)
        self.assertEqual(expected.output_params, sej.output_params)
        self.assertEqual(expected.neg_output_params, sej.neg_output_params)

        self.assertEqual(expected, sej)

    def test_write_odx(self) -> None:
        # Setup jinja environment
        __module_filename = inspect.getsourcefile(odxtools)
        assert isinstance(__module_filename, str)
        templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
        jinja_env.globals["odxraise"] = jinja2_odxraise_helper
        jinja_env.globals["make_xml_attrib"] = make_xml_attrib
        jinja_env.globals["make_bool_xml_attrib"] = make_bool_xml_attrib
        jinja_env.globals["getattr"] = getattr
        jinja_env.globals["hasattr"] = hasattr

        # Small template
        template = jinja_env.from_string("""
            {%- import('macros/printSingleEcuJob.xml.jinja2') as psej %}
            {{psej.printSingleEcuJob(singleecujob)}}
        """)

        rawodx: str = template.render(singleecujob=self.singleecujob_object)

        # Remove whitespace
        actual = rawodx.replace(" ", "")
        expected = self.singleecujob_odx.replace(" ", "")

        # Assert equality of outputted string
        self.maxDiff = None
        self.assertEqual(expected, actual)

        # Assert equality of objects
        # This tests the idempotency of read-write
        sej = SingleEcuJob.from_et(ElementTree.fromstring(rawodx), doc_frags)
        self.assertEqual(self.singleecujob_object, sej)

    def test_default_lists(self) -> None:
        """Test that empty lists are assigned to list-attributes if no explicit value is passed."""
        sej = SingleEcuJob(
            odx_id=OdxLinkId("ID.SomeID", doc_frags),
            oid=None,
            short_name="SN.SomeShortName",
            long_name=None,
            description=None,
            admin_data=None,
            semantic=None,
            audience=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            prog_codes=[
                ProgCode(
                    code_file="abc.jar",
                    library_refs=[],
                    encryption=None,
                    entrypoint=None,
                    syntax="abc",
                    revision="12.34",
                )
            ],
            input_params=NamedItemList(),
            output_params=NamedItemList(),
            neg_output_params=NamedItemList(),
            functional_class_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            sdgs=[],
        )
        self.assertEqual(sej.functional_class_refs, [])
        self.assertEqual(sej.input_params, NamedItemList())
        self.assertEqual(sej.output_params, NamedItemList())
        self.assertEqual(sej.neg_output_params, NamedItemList())
        self.assertEqual(sej.prog_codes[0].library_refs, [])

    def test_resolve_odxlinks(self) -> None:
        ecu_variant_raw = EcuVariantRaw(
            variant_type=DiagLayerType.ECU_VARIANT,
            odx_id=OdxLinkId("ID.bv", doc_frags),
            oid=None,
            short_name="bv",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(),
            functional_classes=NamedItemList([self.context.extensiveTask]),
            diag_data_dictionary_spec=None,
            diag_comms_raw=[self.singleecujob_object],
            requests=NamedItemList(),
            positive_responses=NamedItemList(),
            negative_responses=NamedItemList(),
            global_negative_responses=NamedItemList(),
            additional_audiences=NamedItemList([self.context.specialAudience]),
            import_refs=[],
            state_charts=NamedItemList(),
            sdgs=[],
            parent_refs=[],
            comparam_refs=[],
            ecu_variant_patterns=[],
            diag_variables_raw=[],
            variable_groups=NamedItemList(),
            libraries=NamedItemList([
                Library(
                    short_name="great_lib",
                    long_name=None,
                    description=None,
                    odx_id=OdxLinkId("my.favourite.lib", doc_frags),
                    oid=None,
                    code_file="great_lib.py",
                    encryption=None,
                    syntax="PYTHON",
                    revision="3.141529",
                    entrypoint="i_am_great")
            ]),
            dyn_defined_spec=None,
            sub_components=NamedItemList(),
        )
        ecu_variant = EcuVariant(diag_layer_raw=ecu_variant_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(ecu_variant._build_odxlinks())
        # these objects are actually part of the diag layer's
        # diag_data_dictionary_spec, but it is less hassle to
        # "side-load" them...
        odxlinks.update({
            self.context.extensiveTask.odx_id: self.context.extensiveTask,
            self.context.specialAudience.odx_id: self.context.specialAudience,
            self.context.inputDOP.odx_id: self.context.inputDOP,
            self.context.outputDOP.odx_id: self.context.outputDOP,
            self.context.negOutputDOP.odx_id: self.context.negOutputDOP,
        })

        db = Database()
        db.add_auxiliary_file("abc.jar",
                              BytesIO(b"this is supposed to be a JAR archive, but it isn't (HARR)"))
        db.add_auxiliary_file(
            "great_lib.py",
            BytesIO(b"def i_am_great():\n"
                    b"    print('The greatest algorithm eva!')"))

        ecu_variant._resolve_odxlinks(odxlinks)
        ecu_variant._finalize_init(db, odxlinks)

        self.assertEqual(self.context.extensiveTask,
                         self.singleecujob_object.functional_classes.extensiveTask)
        self.assertEqual(self.context.specialAudience,
                         odxrequire(self.singleecujob_object.audience).enabled_audiences[0])

        self.assertEqual(self.context.inputDOP, self.singleecujob_object.input_params[0].dop_base)
        self.assertEqual(self.context.outputDOP, self.singleecujob_object.output_params[0].dop_base)
        self.assertEqual(self.context.negOutputDOP,
                         self.singleecujob_object.neg_output_params[0].dop)


if __name__ == "__main__":
    unittest.main()
