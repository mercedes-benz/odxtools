# SPDX-License-Identifier: MIT
import inspect
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import jinja2

import odxtools
from examples.somersaultecu import database as somersault_db
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import DocType, OdxDocFragment
from odxtools.specialdata import SpecialData
from odxtools.writepdxfile import (jinja2_odxraise_helper, make_bool_xml_attrib, make_ref_attribs,
                                   make_xml_attrib, set_category_docfrag, set_layer_docfrag)

doc_frags = (OdxDocFragment(doc_name="mecuj_test", doc_type=DocType.MULTIPLE_ECU_JOB_SPEC),)

multiple_ecu_job_xml_str = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <ODX MODEL-VERSION="2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
      <MULTIPLE-ECU-JOB-SPEC ID="odx.mecuj_test">
        <SHORT-NAME>mecuj_test</SHORT-NAME>
        <MULTIPLE-ECU-JOBS>
          <MULTIPLE-ECU-JOB ID="mecuj.MEJ.paloma" SEMANTIC="foo" IS-EXECUTABLE="false">
            <SHORT-NAME>paloma</SHORT-NAME>
            <ADMIN-DATA>
              <LANGUAGE>py-PY</LANGUAGE>
            </ADMIN-DATA>
            <SDGS>
              <SDG SI="LABERTRASH">
                <SDG-CAPTION ID="mecuj.SDGC.foo">
                  <SHORT-NAME>foo</SHORT-NAME>
                </SDG-CAPTION>
                <SD>bla bla</SD>
              </SDG>
              <SDG SI="MORE LABERTRASH">
                <SDG-CAPTION-REF ID-REF="mecuj.SDGC.foo" />
                <SD>blab blab</SD>
              </SDG>
            </SDGS>
            <FUNCT-CLASS-REFS>
              <FUNCT-CLASS-REF ID-REF="somersault.FNC.session" DOCREF="somersault" DOCTYPE="CONTAINER" />
              <FUNCT-CLASS-REF ID-REF="mecuj.FNC.party" />
            </FUNCT-CLASS-REFS>
            <PROG-CODES>
              <PROG-CODE>
                <CODE-FILE>jobs.py</CODE-FILE>
                <SYNTAX>PYTHON3</SYNTAX>
                <REVISION>4.141592</REVISION>
                <ENTRYPOINT>multi_ecu_job</ENTRYPOINT>
              </PROG-CODE>
            </PROG-CODES>
            <INPUT-PARAMS>
              <INPUT-PARAM>
                <SHORT-NAME>my_input_param</SHORT-NAME>
                <PHYSICAL-DEFAULT-VALUE>123</PHYSICAL-DEFAULT-VALUE>
                <DOP-BASE-REF ID-REF="somersault.DOP.uint8" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </INPUT-PARAM>
            </INPUT-PARAMS>
            <OUTPUT-PARAMS>
              <OUTPUT-PARAM ID="mecuj.outparams.my_success" SEMANTIC="GOSSIP">
                <SHORT-NAME>my_success</SHORT-NAME>
                <DOP-BASE-REF ID-REF="somersault.DOP.uint8" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </OUTPUT-PARAM>
            </OUTPUT-PARAMS>
            <NEG-OUTPUT-PARAMS>
              <NEG-OUTPUT-PARAM>
                <SHORT-NAME>my_mistake</SHORT-NAME>
                <DOP-BASE-REF ID-REF="somersault.DOP.uint8" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </NEG-OUTPUT-PARAM>
            </NEG-OUTPUT-PARAMS>
            <DIAG-LAYER-REFS>
              <DIAG-LAYER-REF ID-REF="somersault_lazy" DOCREF="somersault" DOCTYPE="CONTAINER" />
            </DIAG-LAYER-REFS>
            <AUDIENCE IS-DEVELOPMENT="true">
            </AUDIENCE>
          </MULTIPLE-ECU-JOB>
        </MULTIPLE-ECU-JOBS>
        <DIAG-DATA-DICTIONARY-SPEC>
          <ADMIN-DATA>
            <LANGUAGE>hi-HO</LANGUAGE>
          </ADMIN-DATA>
        </DIAG-DATA-DICTIONARY-SPEC>
        <FUNCT-CLASSS>
          <FUNCT-CLASS ID="mecuj.FNC.party">
            <SHORT-NAME>party</SHORT-NAME>
          </FUNCT-CLASS>
        </FUNCT-CLASSS>
        <ADDITIONAL-AUDIENCES>
          <ADDITIONAL-AUDIENCE ID="mecuj.AA.wizards">
            <SHORT-NAME>wizards</SHORT-NAME>
          </ADDITIONAL-AUDIENCE>
        </ADDITIONAL-AUDIENCES>
      </MULTIPLE-ECU-JOB-SPEC>
</ODX>"""

multiple_ecu_job_et = ElementTree.fromstring(multiple_ecu_job_xml_str)


def test_create_multiple_ecu_job_from_et() -> None:
    somersault_db._multiple_ecu_job_specs = NamedItemList()
    somersault_db.add_xml_tree(multiple_ecu_job_et)
    somersault_db.refresh()
    assert len(somersault_db.multiple_ecu_job_specs) == 1

    mecujs = somersault_db.multiple_ecu_job_specs[0]
    assert len(mecujs._build_odxlinks()) == 6
    assert len(mecujs.multiple_ecu_jobs) == 1
    ddds = mecujs.diag_data_dictionary_spec
    assert ddds is not None
    assert ddds.admin_data is not None
    assert ddds.admin_data.language == "hi-HO"
    assert mecujs.functional_classes.party is not None
    assert mecujs.additional_audiences.wizards is not None

    mecuj = mecujs.multiple_ecu_jobs.paloma
    assert mecuj.admin_data is not None
    assert mecuj.admin_data.language == "py-PY"
    assert len(mecuj.sdgs) == 2
    assert len(mecuj.sdgs[0].values) == 1
    assert mecuj.sdgs[0].semantic_info == "LABERTRASH"
    assert mecuj.sdgs[0].sdg_caption_ref is None
    assert mecuj.sdgs[0].sdg_caption is not None
    assert mecuj.sdgs[0].sdg_caption.short_name == "foo"
    assert mecuj.sdgs[1].sdg_caption_ref is not None
    assert mecuj.sdgs[1].sdg_caption is not None
    assert mecuj.sdgs[1].sdg_caption.short_name == "foo"
    sd = mecuj.sdgs[0].values[0]
    assert isinstance(sd, SpecialData)
    assert sd.value == "bla bla"
    sd = mecuj.sdgs[1].values[0]
    assert isinstance(sd, SpecialData)
    assert sd.value == "blab blab"


def test_write_multiple_ecu_job() -> None:
    somersault_db._multiple_ecu_job_specs = NamedItemList()
    somersault_db.add_xml_tree(multiple_ecu_job_et)
    somersault_db.refresh()
    assert len(somersault_db.multiple_ecu_job_specs) == 1

    __module_filename = inspect.getsourcefile(odxtools)
    assert isinstance(__module_filename, str)
    test_jinja_vars: dict[str, Any] = {}
    test_jinja_vars["multiple_ecu_job_spec"] = somersault_db.multiple_ecu_job_specs[0]
    templates_dir = Path(__module_filename).parent / "templates"
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
    jinja_env.globals["odxraise"] = jinja2_odxraise_helper
    jinja_env.globals["make_xml_attrib"] = make_xml_attrib
    jinja_env.globals["make_bool_xml_attrib"] = make_bool_xml_attrib
    jinja_env.globals["set_category_docfrag"] = lambda cname, ctype: set_category_docfrag(
        test_jinja_vars, cname, ctype)
    jinja_env.globals["set_layer_docfrag"] = lambda lname: set_layer_docfrag(test_jinja_vars, lname)
    jinja_env.globals["make_ref_attribs"] = lambda ref: make_ref_attribs(test_jinja_vars, ref)
    jinja_env.globals["getattr"] = getattr
    jinja_env.globals["hasattr"] = hasattr

    template = jinja_env.get_template("multiple-ecu-job-spec.odx-m.xml.jinja2")
    rawodx: str = template.render(test_jinja_vars)

    rawodx2 = '\n'.join(rawodx.split("\n")[0:1] + rawodx.split("\n")[2:])
    expected_xml = multiple_ecu_job_xml_str.replace(" ", "").upper()
    actual_xml = rawodx2.replace(" ", "").upper()

    assert expected_xml == actual_xml
