# SPDX-License-Identifier: MIT
import inspect
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import jinja2

import odxtools
from examples.somersaultecu import database as somersault_db
from odxtools.ecuproxy import EcuProxy
from odxtools.gatewaylogicallink import GatewayLogicalLink
from odxtools.memberlogicallink import MemberLogicalLink
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import DocType, OdxDocFragment
from odxtools.oem import Oem
from odxtools.writepdxfile import (jinja2_odxraise_helper, make_bool_xml_attrib, make_ref_attribs,
                                   make_xml_attrib, set_category_docfrag, set_layer_docfrag)

doc_frags = (OdxDocFragment(doc_name="vehicle_info_test", doc_type=DocType.VEHICLE_INFO_SPEC),)

vehicle_info_spec_xml_str = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <ODX MODEL-VERSION="2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
      <VEHICLE-INFO-SPEC ID="odx.vehicle_info_test">
        <SHORT-NAME>vehicle_info_test</SHORT-NAME>
        <INFO-COMPONENTS>
          <INFO-COMPONENT ID="vis.ic.horse_proxy" xsi:type="ECU-PROXY">
            <SHORT-NAME>horse_proxy</SHORT-NAME>
            <MATCHING-COMPONENTS>
              <MATCHING-COMPONENT>
                <EXPECTED-VALUE>White mare</EXPECTED-VALUE>
                <OUT-PARAM-IF-SNREF SHORT-NAME="sault_time" />
                <DIAG-COMM-REF ID-REF="somersault.service.do_forward_flips" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </MATCHING-COMPONENT>
            </MATCHING-COMPONENTS>
          </INFO-COMPONENT>
          <INFO-COMPONENT ID="vis.ic.limousine" xsi:type="VEHICLE-MODEL">
            <SHORT-NAME>grand_limousine</SHORT-NAME>
            <MATCHING-COMPONENTS>
              <MATCHING-COMPONENT>
                <EXPECTED-VALUE>Black Cap</EXPECTED-VALUE>
                <OUT-PARAM-IF-SNREF SHORT-NAME="status" />
                <DIAG-COMM-REF ID-REF="somersault.service.tester_present" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </MATCHING-COMPONENT>
            </MATCHING-COMPONENTS>
          </INFO-COMPONENT>
          <INFO-COMPONENT ID="vis.ic.1842" xsi:type="MODEL-YEAR">
            <SHORT-NAME>1842</SHORT-NAME>
            <MATCHING-COMPONENTS>
              <MATCHING-COMPONENT>
                <EXPECTED-VALUE>1842</EXPECTED-VALUE>
                <OUT-PARAM-IF-SNPATHREF SHORT-NAME-PATH="last_pos_resonse.forward_grudging.num_flips_done" />
                <DIAG-COMM-REF ID-REF="somersault.service.report_status" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </MATCHING-COMPONENT>
            </MATCHING-COMPONENTS>
          </INFO-COMPONENT>
          <INFO-COMPONENT ID="vis.ic.oem" xsi:type="OEM">
            <SHORT-NAME>Hansom</SHORT-NAME>
            <MATCHING-COMPONENTS>
              <MATCHING-COMPONENT>
                <EXPECTED-VALUE>Hansom</EXPECTED-VALUE>
                <OUT-PARAM-IF-SNREF SHORT-NAME="schroedingers_god" />
                <DIAG-COMM-REF ID-REF="somersault.service.schroedinger" DOCREF="somersault" DOCTYPE="CONTAINER" />
              </MATCHING-COMPONENT>
            </MATCHING-COMPONENTS>
          </INFO-COMPONENT>
        </INFO-COMPONENTS>
        <VEHICLE-INFORMATIONS>
          <VEHICLE-INFORMATION>
            <SHORT-NAME>coach_info</SHORT-NAME>
            <INFO-COMPONENT-REFS>
              <INFO-COMPONENT-REF ID-REF="vis.ic.oem" />
            </INFO-COMPONENT-REFS>
            <VEHICLE-CONNECTORS>
              <VEHICLE-CONNECTOR>
                <SHORT-NAME>seat_connector</SHORT-NAME>
                <VEHICLE-CONNECTOR-PINS>
                  <VEHICLE-CONNECTOR-PIN ID="vis.seat_conn.ground" TYPE="MINUS">
                    <SHORT-NAME>ground</SHORT-NAME>
                    <PIN-NUMBER>1</PIN-NUMBER>
                  </VEHICLE-CONNECTOR-PIN>
                  <VEHICLE-CONNECTOR-PIN ID="vis.seat_conn.can_hi" TYPE="HI">
                    <SHORT-NAME>can_hi</SHORT-NAME>
                    <PIN-NUMBER>2</PIN-NUMBER>
                  </VEHICLE-CONNECTOR-PIN>
                  <VEHICLE-CONNECTOR-PIN ID="vis.seat_conn.can_lo" TYPE="LOW">
                    <SHORT-NAME>can_lo</SHORT-NAME>
                    <PIN-NUMBER>3</PIN-NUMBER>
                  </VEHICLE-CONNECTOR-PIN>
                </VEHICLE-CONNECTOR-PINS>
              </VEHICLE-CONNECTOR>
            </VEHICLE-CONNECTORS>
            <LOGICAL-LINKS>
              <LOGICAL-LINK ID="vis.ll.gateway" xsi:type="GATEWAY-LOGICAL-LINK">
                <SHORT-NAME>gateway</SHORT-NAME>
                <GATEWAY-LOGICAL-LINK-REFS>
                  <GATEWAY-LOGICAL-LINK-REF ID-REF="vis.ll.gateway" />
                </GATEWAY-LOGICAL-LINK-REFS>
                <PHYSICAL-VEHICLE-LINK-REF ID-REF="vis.pvs.phys_vehicle_link" />
                <PROTOCOL-REF ID-REF="somersault.protocol" DOCREF="somersault" DOCTYPE="CONTAINER" />
                <BASE-VARIANT-REF ID-REF="somersault.base_variant" DOCREF="somersault" DOCTYPE="CONTAINER" />
                <ECU-PROXY-REFS>
                  <ECU-PROXY-REF ID-REF="vis.ic.horse_proxy" />
                </ECU-PROXY-REFS>
                <LINK-COMPARAM-REFS>
                  <LINK-COMPARAM-REF ID-REF="ISO_11898_2_DWCAN.CP_CanBaudrateRecord" DOCREF="ISO_11898_2_DWCAN" DOCTYPE="COMPARAM-SUBSET">
                    <SIMPLE-VALUE>0</SIMPLE-VALUE>
                    <DESC><p>This is a horse-pulled coach!</p></DESC>
                  </LINK-COMPARAM-REF>
                </LINK-COMPARAM-REFS>
                <PROT-STACK-SNREF SHORT-NAME="unicorn_prot_stack" />
                <SEMANTIC>IAmGroot</SEMANTIC>
              </LOGICAL-LINK>
              <LOGICAL-LINK ID="vis.ll.member" xsi:type="MEMBER-LOGICAL-LINK">
                <SHORT-NAME>member</SHORT-NAME>
                <GATEWAY-LOGICAL-LINK-REFS>
                  <GATEWAY-LOGICAL-LINK-REF ID-REF="vis.ll.member" />
                </GATEWAY-LOGICAL-LINK-REFS>
                <PHYSICAL-VEHICLE-LINK-REF ID-REF="vis.pvs.phys_vehicle_link" />
                <PROTOCOL-REF ID-REF="somersault.protocol" DOCREF="somersault" DOCTYPE="CONTAINER" />
                <BASE-VARIANT-REF ID-REF="somersault.base_variant" DOCREF="somersault" DOCTYPE="CONTAINER" />
                <ECU-PROXY-REFS>
                  <ECU-PROXY-REF ID-REF="vis.ic.horse_proxy" />
                </ECU-PROXY-REFS>
                <LINK-COMPARAM-REFS>
                  <LINK-COMPARAM-REF ID-REF="ISO_11898_2_DWCAN.CP_CanBaudrateRecord" DOCREF="ISO_11898_2_DWCAN" DOCTYPE="COMPARAM-SUBSET">
                    <SIMPLE-VALUE>0</SIMPLE-VALUE>
                    <DESC><p>This is a horse-pulled coach!</p></DESC>
                  </LINK-COMPARAM-REF>
                </LINK-COMPARAM-REFS>
                <PROT-STACK-SNREF SHORT-NAME="unicorn_prot_stack" />
              </LOGICAL-LINK>
            </LOGICAL-LINKS>
            <ECU-GROUPS>
              <ECU-GROUP>
                <SHORT-NAME>my_ecu_group</SHORT-NAME>
                <GROUP-MEMBERS>
                  <GROUP-MEMBER>
                    <BASE-VARIANT-REF ID-REF="somersault.base_variant" DOCREF="somersault" DOCTYPE="CONTAINER" />
                    <FUNCT-RESOLUTION-LINK-REF ID-REF="vis.ll.gateway" />
                    <PHYS-RESOLUTION-LINK-REF ID-REF="vis.ll.member" />
                  </GROUP-MEMBER>
                </GROUP-MEMBERS>
              </ECU-GROUP>
            </ECU-GROUPS>
            <PHYSICAL-VEHICLE-LINKS>
              <PHYSICAL-VEHICLE-LINK ID="vis.pvs.phys_vehicle_link" TYPE="LINKYLINK">
                <SHORT-NAME>my_phys_vehicle_link</SHORT-NAME>
                <VEHICLE-CONNECTOR-PIN-REFS>
                  <VEHICLE-CONNECTOR-PIN-REF ID-REF="vis.seat_conn.ground" />
                </VEHICLE-CONNECTOR-PIN-REFS>
                <LINK-COMPARAM-REFS>
                  <LINK-COMPARAM-REF ID-REF="ISO_11898_2_DWCAN.CP_CanBaudrateRecord" DOCREF="ISO_11898_2_DWCAN" DOCTYPE="COMPARAM-SUBSET">
                    <SIMPLE-VALUE>0</SIMPLE-VALUE>
                    <DESC><p>This is a horse-pulled coach!</p></DESC>
                  </LINK-COMPARAM-REF>
                </LINK-COMPARAM-REFS>
              </PHYSICAL-VEHICLE-LINK>
            </PHYSICAL-VEHICLE-LINKS>
          </VEHICLE-INFORMATION>
        </VEHICLE-INFORMATIONS>
      </VEHICLE-INFO-SPEC>
    </ODX>"""

vehicle_info_spec_et = ElementTree.fromstring(vehicle_info_spec_xml_str)


def test_create_vehicle_info_spec_from_et() -> None:
    somersault_db._vehicle_info_specs = NamedItemList()
    somersault_db.add_xml_tree(vehicle_info_spec_et)
    somersault_db.refresh()
    assert len(somersault_db.vehicle_info_specs) == 1

    vehicle_info_spec = somersault_db.vehicle_info_specs.vehicle_info_test
    assert len(vehicle_info_spec._build_odxlinks()) == 11

    assert len(vehicle_info_spec.info_components) == 4
    ic = vehicle_info_spec.info_components.horse_proxy
    assert isinstance(ic, EcuProxy)
    assert ic.component_type.value == "ECU-PROXY"

    assert len(ic.matching_components) == 1
    mc = ic.matching_components[0]

    assert mc.expected_value == "White mare"
    assert mc.out_param_if_snref == "sault_time"
    assert mc.diag_comm is not None
    assert mc.diag_comm.short_name == "do_forward_flips"

    ic = vehicle_info_spec.info_components._1842
    assert ic.matching_components[0].out_param_if_snref is None
    assert ic.matching_components[
        0].out_param_if_snpathref == "last_pos_resonse.forward_grudging.num_flips_done"

    assert len(vehicle_info_spec.vehicle_informations) == 1
    vi = vehicle_info_spec.vehicle_informations.coach_info

    assert isinstance(vi.info_components.Hansom, Oem)

    assert len(vi.vehicle_connectors) == 1
    vc = vi.vehicle_connectors.seat_connector

    assert len(vc.vehicle_connector_pins) == 3
    pin1 = vc.vehicle_connector_pins.ground
    assert pin1.pin_type.value == "MINUS"
    assert pin1.pin_number == 1

    assert len(vi.logical_links) == 2
    gl = vi.logical_links.gateway
    assert isinstance(gl, GatewayLogicalLink)
    assert gl.link_type.value == "GATEWAY-LOGICAL-LINK"
    assert len(gl.gateway_logical_links) == 1
    assert isinstance(gl.gateway_logical_links.gateway, GatewayLogicalLink)

    assert gl.physical_vehicle_link is not None
    assert gl.protocol is not None
    assert gl.protocol.short_name == "somersault_protocol"
    assert gl.base_variant is not None
    assert gl.base_variant.short_name == "somersault_base_variant"
    assert len(gl.ecu_proxies) == 1
    assert gl.ecu_proxies.horse_proxy is not None
    assert len(gl.link_comparam_refs) == 1
    assert gl.link_comparam_refs.CP_CanBaudrateRecord is not None
    assert gl.link_comparam_refs.CP_CanBaudrateRecord.simple_value == "0"
    assert gl.prot_stack_snref == "unicorn_prot_stack"
    assert gl.semantic == "IAmGroot"

    assert len(vi.ecu_groups) == 1
    ecug = vi.ecu_groups.my_ecu_group
    assert len(ecug.group_members) == 1
    ecugm = ecug.group_members[0]
    assert ecugm.base_variant is not None
    assert isinstance(ecugm.funct_resolution_link, GatewayLogicalLink)
    assert isinstance(ecugm.phys_resolution_link, MemberLogicalLink)

    assert len(vi.physical_vehicle_links) == 1
    pvl = vi.physical_vehicle_links.my_phys_vehicle_link
    assert len(pvl.vehicle_connector_pin_refs) == 1
    assert len(pvl.vehicle_connector_pins) == 1
    assert pvl.vehicle_connector_pins.ground.pin_number == 1
    assert len(pvl.link_comparam_refs) == 1
    assert pvl.link_comparam_refs.CP_CanBaudrateRecord is not None
    assert pvl.link_comparam_refs.CP_CanBaudrateRecord.simple_value == '0'


def test_write_vehicle_info_spec() -> None:
    somersault_db._vehicle_info_specs = NamedItemList()
    somersault_db.add_xml_tree(vehicle_info_spec_et)
    somersault_db.refresh()
    assert len(somersault_db.vehicle_info_specs) == 1

    __module_filename = inspect.getsourcefile(odxtools)
    assert isinstance(__module_filename, str)
    test_jinja_vars: dict[str, Any] = {}
    test_jinja_vars["vehicle_info_spec"] = somersault_db.vehicle_info_specs[0]
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

    template = jinja_env.get_template("vehicle_info_spec.odx-v.xml.jinja2")
    rawodx: str = template.render(test_jinja_vars)

    rawodx2 = '\n'.join(rawodx.split("\n")[0:1] + rawodx.split("\n")[2:])
    expected_xml = vehicle_info_spec_xml_str.replace(" ", "").upper()
    actual_xml = rawodx2.replace(" ", "").upper()

    assert expected_xml == actual_xml
