# SPDX-License-Identifier: MIT
import inspect
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import jinja2

import odxtools
from examples.somersaultecu import database as somersault_db
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import DocType, OdxDocFragment
from odxtools.writepdxfile import (jinja2_odxraise_helper, make_bool_xml_attrib, make_ref_attribs,
                                   make_xml_attrib, set_category_docfrag, set_layer_docfrag)

from .test_multiple_ecu_jobs import multiple_ecu_job_et
from .test_vehicle_info_spec import vehicle_info_spec_et

doc_frags = (OdxDocFragment(doc_name="mecuj_test", doc_type=DocType.FUNCTION_DICTIONARY_SPEC),)

function_dictionary_xml_str = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ODX MODEL-VERSION="2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
  <FUNCTION-DICTIONARY ID="odx.fd_test">
    <SHORT-NAME>fd_test</SHORT-NAME>
    <FUNCTION-NODES>
      <FUNCTION-NODE ID="fd_test.function_node0">
        <SHORT-NAME>function_node0</SHORT-NAME>
        <AUDIENCE IS-DEVELOPMENT="true">
        </AUDIENCE>
        <FUNCTION-IN-PARAMS>
          <FUNCTION-IN-PARAM>
            <SHORT-NAME>function_in_param0</SHORT-NAME>
            <UNIT-REF ID-REF="somersault.unit.second" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            <PHYSICAL-TYPE BASE-DATA-TYPE="A_INT32" />
            <IN-PARAM-IF-SNREF SHORT-NAME="some_param_name"/>
            <FUNCTION-DIAG-COMM-CONNECTOR>
              <LOGICAL-LINK-REF ID-REF="vis.ll.gateway" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
              <DIAG-COMM-REF ID-REF="somersault.service.session_start" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            </FUNCTION-DIAG-COMM-CONNECTOR>
          </FUNCTION-IN-PARAM>
        </FUNCTION-IN-PARAMS>
        <FUNCTION-OUT-PARAMS>
          <FUNCTION-OUT-PARAM>
            <SHORT-NAME>function_out_param0</SHORT-NAME>
            <UNIT-REF ID-REF="somersault.unit.celsius" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            <PHYSICAL-TYPE BASE-DATA-TYPE="A_UINT32" />
            <OUT-PARAM-IF-SNREF SHORT-NAME="some_out_param_name"/>
            <FUNCTION-DIAG-COMM-CONNECTOR>
              <LOGICAL-LINK-REF ID-REF="vis.ll.member" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
              <DIAG-COMM-REF ID-REF="somersault.service.compulsory_program" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            </FUNCTION-DIAG-COMM-CONNECTOR>
          </FUNCTION-OUT-PARAM>
        </FUNCTION-OUT-PARAMS>
        <COMPONENT-CONNECTORS>
          <COMPONENT-CONNECTOR>
            <ECU-VARIANT-REFS>
              <ECU-VARIANT-REF ID-REF="somersault_lazy" DOCREF="somersault" DOCTYPE="CONTAINER" />
            </ECU-VARIANT-REFS>
            <BASE-VARIANT-REF ID-REF="somersault.base_variant" DOCREF="somersault" DOCTYPE="CONTAINER" />
            <DIAG-OBJECT-CONNECTOR ID="fd_test.my_do_conn" >
              <SHORT-NAME>my_do_conn</SHORT-NAME>
              <FUNCTION-DIAG-COMM-CONNECTORS>
                <FUNCTION-DIAG-COMM-CONNECTOR>
                  <LOGICAL-LINK-REF ID-REF="vis.ll.gateway" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
                  <DIAG-COMM-REF ID-REF="somersault.service.session_start" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                </FUNCTION-DIAG-COMM-CONNECTOR>
              </FUNCTION-DIAG-COMM-CONNECTORS>
              <TABLE-ROW-CONNECTORS>
                <TABLE-ROW-CONNECTOR>
                  <SHORT-NAME>my_tr_conn</SHORT-NAME>
                  <TABLE-REF ID-REF="somersault.table.last_flip_details" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                  <TABLE-ROW-SNREF SHORT-NAME="forward_grudging" />
                </TABLE-ROW-CONNECTOR>
              </TABLE-ROW-CONNECTORS>
              <!--
                  TODO: the somersault example does not yet feature environment datas
                  <ENV-DATA-CONNECTORS>
                  <ENV-DATA-CONNECTOR>
                  <SHORT-NAME>my_ed_conn</SHORT-NAME>
                  <ENV-DATA-DESC-REF ID-REF="TODO" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                  <ENV-DATA-SNREF SHORT-NAME="TODO" />
                  </ENV-DATA-CONNECTOR>
                  </ENV-DATA-CONNECTORS>
              -->
              <!--
                  TODO: the somersault example does not yet feature DTCs
                  <DTC-CONNECTORS>
                  <DTC-CONNECTOR>
                  <SHORT-NAME>my_dtc_conn</SHORT-NAME>
                  <DTC-DOP-REF ID-REF="TODO" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                  <DTC-SNREF SHORT-NAME="TODO" />
                  </DTC-CONNECTOR>
                  </DTC-CONNECTORS>
              -->
            </DIAG-OBJECT-CONNECTOR>
          </COMPONENT-CONNECTOR>
          <COMPONENT-CONNECTOR>
            <DIAG-OBJECT-CONNECTOR-REF ID-REF="fd_test.my_do_conn" />
          </COMPONENT-CONNECTOR>
        </COMPONENT-CONNECTORS>
        <MULTIPLE-ECU-JOB-REFS>
          <MULTIPLE-ECU-JOB-REF ID-REF="mecuj.MEJ.paloma" DOCREF="mecuj_test" DOCTYPE="MULTIPLE-ECU-JOB-SPEC"/>
        </MULTIPLE-ECU-JOB-REFS>
        <ADMIN-DATA>
          <LANGUAGE>en-ZA</LANGUAGE>
        </ADMIN-DATA>
        <SDG SI="stupid testing">
        </SDG>
      </FUNCTION-NODE>
    </FUNCTION-NODES>
    <FUNCTION-NODE-GROUPS>
      <FUNCTION-NODE-GROUP ID="fd_test.function_node_group0">
        <SHORT-NAME>function_node_group0</SHORT-NAME>
        <AUDIENCE IS-DEVELOPMENT="true">
        </AUDIENCE>
        <FUNCTION-IN-PARAMS>
          <FUNCTION-IN-PARAM>
            <SHORT-NAME>function_node_group_in_param0</SHORT-NAME>
            <UNIT-REF ID-REF="somersault.unit.minute" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            <PHYSICAL-TYPE BASE-DATA-TYPE="A_INT32" />
            <IN-PARAM-IF-SNREF SHORT-NAME="some_param_name"/>
            <FUNCTION-DIAG-COMM-CONNECTOR>
              <LOGICAL-LINK-REF ID-REF="vis.ll.member" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
              <DIAG-COMM-REF ID-REF="somersault.service.session_start" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            </FUNCTION-DIAG-COMM-CONNECTOR>
          </FUNCTION-IN-PARAM>
        </FUNCTION-IN-PARAMS>
        <FUNCTION-OUT-PARAMS>
          <FUNCTION-OUT-PARAM>
            <SHORT-NAME>function_node_group_out_param0</SHORT-NAME>
            <UNIT-REF ID-REF="somersault.unit.celsius" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            <PHYSICAL-TYPE BASE-DATA-TYPE="A_INT32" />
            <OUT-PARAM-IF-SNREF SHORT-NAME="some_other_param_name"/>
            <FUNCTION-DIAG-COMM-CONNECTOR>
              <LOGICAL-LINK-REF ID-REF="vis.ll.gateway" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
              <DIAG-COMM-REF ID-REF="somersault.service.session_start" DOCREF="somersault" DOCTYPE="CONTAINER"/>
            </FUNCTION-DIAG-COMM-CONNECTOR>
          </FUNCTION-OUT-PARAM>
        </FUNCTION-OUT-PARAMS>
        <FUNCTION-NODE-REFS>
          <FUNCTION-NODE-REF ID-REF="fd_test.function_node0"/>
        </FUNCTION-NODE-REFS>
        <FUNCTION-NODE-GROUPS>
          <FUNCTION-NODE-GROUP ID="fd_test.function_node_group_nested">
            <SHORT-NAME>function_node_group_nested</SHORT-NAME>
            <AUDIENCE IS-DEVELOPMENT="true">
            </AUDIENCE>
            <FUNCTION-IN-PARAMS>
              <FUNCTION-IN-PARAM>
                <SHORT-NAME>function_node_group_nested_in_param0</SHORT-NAME>
                <UNIT-REF ID-REF="somersault.unit.second" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                <PHYSICAL-TYPE BASE-DATA-TYPE="A_INT32" />
                <IN-PARAM-IF-SNREF SHORT-NAME="some_param_name"/>
                <FUNCTION-DIAG-COMM-CONNECTOR>
                  <LOGICAL-LINK-REF ID-REF="vis.ll.gateway" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
                  <DIAG-COMM-REF ID-REF="somersault.service.session_start" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                </FUNCTION-DIAG-COMM-CONNECTOR>
              </FUNCTION-IN-PARAM>
            </FUNCTION-IN-PARAMS>
            <FUNCTION-OUT-PARAMS>
              <FUNCTION-OUT-PARAM>
                <SHORT-NAME>function_node_group_nested_out_param0</SHORT-NAME>
                <UNIT-REF ID-REF="somersault.unit.minute" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                <PHYSICAL-TYPE BASE-DATA-TYPE="A_INT32" />
                <OUT-PARAM-IF-SNREF SHORT-NAME="some_param_name"/>
                <FUNCTION-DIAG-COMM-CONNECTOR>
                  <LOGICAL-LINK-REF ID-REF="vis.ll.member" DOCREF="vehicle_info_test" DOCTYPE="VEHICLE-INFO-SPEC"/>
                  <DIAG-COMM-REF ID-REF="somersault.service.tester_present" DOCREF="somersault" DOCTYPE="CONTAINER"/>
                </FUNCTION-DIAG-COMM-CONNECTOR>
              </FUNCTION-OUT-PARAM>
            </FUNCTION-OUT-PARAMS>
          </FUNCTION-NODE-GROUP>
        </FUNCTION-NODE-GROUPS>
      </FUNCTION-NODE-GROUP>
    </FUNCTION-NODE-GROUPS>
  </FUNCTION-DICTIONARY>
</ODX>"""

function_dictionary_et = ElementTree.fromstring(function_dictionary_xml_str)


def test_create_function_dictionary_from_et() -> None:
    somersault_db._function_dictionaries = NamedItemList()
    somersault_db._vehicle_info_specs = NamedItemList()
    somersault_db._multiple_ecu_job_specs = NamedItemList()
    somersault_db.add_xml_tree(function_dictionary_et)
    somersault_db.add_xml_tree(vehicle_info_spec_et)
    somersault_db.add_xml_tree(multiple_ecu_job_et)
    somersault_db.refresh()
    assert len(somersault_db.function_dictionaries) == 1

    fd = somersault_db.function_dictionaries[0]
    assert len(fd._build_odxlinks()) == 5
    assert len(somersault_db.function_dictionaries) == 1

    assert len(fd.function_nodes) == 1
    fn = fd.function_nodes.function_node0

    assert fn.audience is not None
    assert fn.audience.is_development

    assert len(fn.function_in_params) == 1
    fip = fn.function_in_params.function_in_param0
    assert fip.unit is not None
    assert fip.unit.short_name == "second"
    assert fip.physical_type.base_data_type.value == "A_INT32"
    assert fip.in_param_if_snref == "some_param_name"

    fdcc = fip.function_diag_comm_connector
    assert fdcc is not None

    ll = fdcc.logical_link
    assert ll is not None
    assert ll.link_type.value == "GATEWAY-LOGICAL-LINK"

    dc = fdcc.diag_comm
    assert dc.short_name == "session_start"

    assert len(fn.function_out_params) == 1
    fop = fn.function_out_params.function_out_param0
    assert fop.unit is not None
    assert fop.unit.short_name == "celsius"
    assert fop.physical_type.base_data_type.value == "A_UINT32"
    assert fop.out_param_if_snref == "some_out_param_name"
    fdcc = fop.function_diag_comm_connector
    assert fdcc is not None

    ll = fdcc.logical_link
    assert ll is not None
    assert ll.link_type.value == "MEMBER-LOGICAL-LINK"

    dc = fdcc.diag_comm
    assert dc.short_name == "compulsory_program"

    assert len(fn.component_connectors) == 2
    cc = fn.component_connectors[0]
    assert len(cc.ecu_variants) == 1
    assert cc.ecu_variants.somersault_lazy is not None
    assert cc.base_variant is not None

    assert cc.diag_object_connector_ref is None
    assert cc.diag_object_connector is not None
    assert cc.diag_object_connector.short_name == "my_do_conn"

    cc = fn.component_connectors[1]
    assert cc.diag_object_connector_ref is not None
    assert cc.diag_object_connector is not None
    assert cc.diag_object_connector.short_name == "my_do_conn"

    assert len(fn.multiple_ecu_jobs) == 1
    assert fn.multiple_ecu_jobs[0].short_name == "paloma"

    assert fn.admin_data is not None
    assert fn.admin_data.language == "en-ZA"

    assert fn.sdg is not None
    assert fn.sdg.semantic_info == "stupid testing"

    assert len(fd.function_node_groups) == 1
    fng = fd.function_node_groups.function_node_group0
    assert fng.audience is not None
    assert fng.audience.is_development
    assert len(fng.function_nodes) == 1
    assert fng.function_nodes.function_node0 is not None
    assert len(fng.function_node_groups) == 1
    assert fng.function_node_groups.function_node_group_nested is not None


def test_write_function_dictionary() -> None:
    somersault_db._function_dictionaries = NamedItemList()
    somersault_db._vehicle_info_specs = NamedItemList()
    somersault_db._multiple_ecu_job_specs = NamedItemList()
    somersault_db.add_xml_tree(function_dictionary_et)
    somersault_db.add_xml_tree(vehicle_info_spec_et)
    somersault_db.add_xml_tree(multiple_ecu_job_et)
    somersault_db.refresh()
    assert len(somersault_db.function_dictionaries) == 1

    __module_filename = inspect.getsourcefile(odxtools)
    assert isinstance(__module_filename, str)
    test_jinja_vars: dict[str, Any] = {}
    test_jinja_vars["function_dictionary"] = somersault_db.function_dictionaries[0]
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

    template = jinja_env.get_template("function_dictionary.odx-fd.xml.jinja2")
    rawodx: str = template.render(test_jinja_vars)

    rawodx2 = '\n'.join(rawodx.split("\n")[0:1] + rawodx.split("\n")[2:])
    expected_xml = function_dictionary_xml_str.replace(" ", "").upper()
    expected_xml = re.sub(r"<!--.*-->\s*", "", expected_xml, flags=re.DOTALL)
    actual_xml = rawodx2.replace(" ", "").upper()

    assert expected_xml == actual_xml
