# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import inspect
import os
import unittest
from typing import NamedTuple, cast
from xml.etree import ElementTree

import jinja2

import odxtools
from odxtools.audience import AdditionalAudience, Audience
from odxtools.compumethods import CompuScale, Limit, LinearCompuMethod, TexttableCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diaglayer import DiagLayer, DiagLayerRaw
from odxtools.diaglayertype import DiagLayerType
from odxtools.functionalclass import FunctionalClass
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.physicaltype import PhysicalType
from odxtools.singleecujob import InputParam, NegOutputParam, OutputParam, ProgCode, SingleEcuJob
from odxtools.utils import short_name_as_id
from odxtools.write_pdx_file import jinja2_odxraise_helper, make_bool_xml_attrib, make_xml_attrib

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
                short_name="extensiveTask",
                long_name=None,
                description=None,
            ),
            specialAudience=AdditionalAudience(
                odx_id=OdxLinkId("ID.specialAudience", doc_frags),
                short_name="specialAudience",
                long_name=None,
                description=None,
            ),
            inputDOP=DataObjectProperty(
                odx_id=OdxLinkId("ID.inputDOP", doc_frags),
                short_name="inputDOP",
                long_name=None,
                description=None,
                is_visible_raw=None,
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
                    internal_to_phys=[
                        CompuScale("yes", lower_limit=Limit(0), compu_const="Yes!"),
                        CompuScale("no", lower_limit=Limit(1), compu_const="No!"),
                    ],
                    internal_type=DataType.A_UINT32,
                ),
                unit_ref=None,
                sdgs=[],
            ),
            outputDOP=DataObjectProperty(
                odx_id=OdxLinkId("ID.outputDOP", doc_frags),
                short_name="outputDOP",
                long_name=None,
                description=None,
                is_visible_raw=None,
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
                    offset=1,
                    factor=-1,
                    denominator=1,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32,
                    internal_lower_limit=None,
                    internal_upper_limit=None,
                ),
                unit_ref=None,
                sdgs=[],
            ),
            negOutputDOP=DataObjectProperty(
                odx_id=OdxLinkId("ID.negOutputDOP", doc_frags),
                short_name="negOutputDOP",
                long_name=None,
                description=None,
                is_visible_raw=None,
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
                    offset=1,
                    factor=-1,
                    denominator=1,
                    internal_type=DataType.A_UINT32,
                    physical_type=DataType.A_UINT32,
                    internal_lower_limit=None,
                    internal_upper_limit=None,
                ),
                unit_ref=None,
                sdgs=[],
            ),
        )

        input_params = [
            InputParam(
                oid=None,
                short_name="inputParam",
                long_name=None,
                description=None,
                semantic=None,
                physical_default_value="Yes!",
                dop_base_ref=OdxLinkRef.from_id(self.context.inputDOP.odx_id),
            )
        ]
        output_params = [
            OutputParam(
                odx_id=OdxLinkId("ID.outputParam", doc_frags),
                oid=None,
                semantic="DATA",
                short_name="outputParam",
                long_name="The Output Param",
                description="<p>The one and only output of this job.</p>",
                dop_base_ref=OdxLinkRef.from_id(self.context.outputDOP.odx_id),
            )
        ]
        neg_output_params = [
            NegOutputParam(
                short_name="NegativeOutputParam",
                long_name=None,
                description="<p>The one and only output of this job.</p>",
                dop_base_ref=OdxLinkRef.from_id(self.context.negOutputDOP.odx_id),
            )
        ]

        self.singleecujob_object = SingleEcuJob(
            odx_id=OdxLinkId("ID.JumpStart", doc_frags),
            oid=None,
            short_name="JumpStart",
            long_name=None,
            description=None,
            admin_data=None,
            semantic=None,
            functional_class_refs=[OdxLinkRef.from_id(self.context.extensiveTask.odx_id)],
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
                        <DESC>\n{output_params[0].description}\n</DESC>
                        <DOP-BASE-REF ID-REF="{output_params[0].dop_base_ref.ref_id}"/>
                    </OUTPUT-PARAM>
                </OUTPUT-PARAMS>
                <NEG-OUTPUT-PARAMS>
                    <NEG-OUTPUT-PARAM>
                        <SHORT-NAME>{neg_output_params[0].short_name}</SHORT-NAME>
                        <DESC>\n{neg_output_params[0].description}\n</DESC>
                        <DOP-BASE-REF ID-REF="{neg_output_params[0].dop_base_ref.ref_id}"/>
                    </NEG-OUTPUT-PARAM>
                </NEG-OUTPUT-PARAMS>
            </SINGLE-ECU-JOB>
        """

    def test_read_odx(self):
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
        self.assertEqual(expected, actual)

        # Assert equality of objects
        # This tests the idempotency of read-write
        sej = SingleEcuJob.from_et(ElementTree.fromstring(rawodx), doc_frags)
        self.assertEqual(self.singleecujob_object, sej)

    def test_default_lists(self):
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
            input_params=[],
            output_params=[],
            neg_output_params=[],
            functional_class_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            sdgs=[],
        )
        self.assertEqual(sej.functional_class_refs, [])
        self.assertEqual(sej.input_params, NamedItemList(short_name_as_id))
        self.assertEqual(sej.output_params, NamedItemList(short_name_as_id))
        self.assertEqual(sej.neg_output_params, NamedItemList(short_name_as_id))
        self.assertEqual(sej.prog_codes[0].library_refs, [])

    def test_resolve_odxlinks(self):
        diag_layer_raw = DiagLayerRaw(
            variant_type=DiagLayerType.BASE_VARIANT,
            odx_id=OdxLinkId("ID.bv", doc_frags),
            short_name="bv",
            long_name=None,
            description=None,
            admin_data=None,
            company_datas=NamedItemList(short_name_as_id),
            functional_classes=NamedItemList(short_name_as_id, [self.context.extensiveTask]),
            diag_data_dictionary_spec=None,
            diag_comms=[self.singleecujob_object],
            requests=NamedItemList(short_name_as_id),
            positive_responses=NamedItemList(short_name_as_id),
            negative_responses=NamedItemList(short_name_as_id),
            global_negative_responses=NamedItemList(short_name_as_id),
            additional_audiences=NamedItemList(short_name_as_id, [self.context.specialAudience]),
            import_refs=[],
            state_charts=NamedItemList(short_name_as_id),
            sdgs=[],
            parent_refs=[],
            communication_parameters=[],
            ecu_variant_patterns=[],
        )
        dl = DiagLayer(diag_layer_raw=diag_layer_raw)
        odxlinks = OdxLinkDatabase()
        odxlinks.update(dl._build_odxlinks())
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

        dl._resolve_odxlinks(odxlinks)
        dl._finalize_init(odxlinks)

        self.assertEqual(self.context.extensiveTask,
                         self.singleecujob_object.functional_classes.extensiveTask)
        self.assertEqual(self.context.specialAudience,
                         self.singleecujob_object.audience.enabled_audiences[0])

        self.assertEqual(self.context.inputDOP, self.singleecujob_object.input_params[0].dop)
        self.assertEqual(self.context.outputDOP, self.singleecujob_object.output_params[0].dop)
        self.assertEqual(self.context.negOutputDOP,
                         self.singleecujob_object.neg_output_params[0].dop)


if __name__ == "__main__":
    unittest.main()
