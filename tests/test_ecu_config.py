# SPDX-License-Identifier: MIT
import inspect
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import jinja2
from bincopy import BinFile

import odxtools
from examples.somersaultecu import database as somersault_db
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import DocType, OdxDocFragment
from odxtools.writepdxfile import (jinja2_odxraise_helper, make_bool_xml_attrib, make_ref_attribs,
                                   make_xml_attrib, set_category_docfrag, set_layer_docfrag)

doc_frags = (OdxDocFragment(doc_name="ecu_config_test", doc_type=DocType.ECU_CONFIG),)

ecu_config_xml_str = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <ODX MODEL-VERSION="2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
      <ECU-CONFIG ID="odx.ecu_config_test">
        <SHORT-NAME>ecu_config_test</SHORT-NAME>
        <CONFIG-DATAS>
          <CONFIG-DATA>
            <SHORT-NAME>ect_config_data0</SHORT-NAME>
            <VALID-BASE-VARIANTS>
              <VALID-BASE-VARIANT>
                <ECU-VARIANT-SNREFS>
                  <ECU-VARIANT-SNREF SHORT-NAME="somersault_lazy" />
                </ECU-VARIANT-SNREFS>
                <BASE-VARIANT-SNREF SHORT-NAME="somersault_base_variant" />
              </VALID-BASE-VARIANT>
            </VALID-BASE-VARIANTS>
            <CONFIG-RECORDS>
              <CONFIG-RECORD>
                <SHORT-NAME>my_config_record</SHORT-NAME>
                <CONFIG-ID-ITEM>
                  <SHORT-NAME>my_config_id</SHORT-NAME>
                  <BYTE-POSITION> 123 </BYTE-POSITION>
                  <BIT-POSITION> 2 </BIT-POSITION>
                  <DATA-OBJECT-PROP-REF ID-REF="somersault.DOP.temperature" DOCREF="somersault" DOCTYPE="CONTAINER" />
                </CONFIG-ID-ITEM>
                <DIAG-COMM-DATA-CONNECTORS>
                  <DIAG-COMM-DATA-CONNECTOR>
                    <UNCOMPRESSED-SIZE> 432 </UNCOMPRESSED-SIZE>
                    <SOURCE-START-ADDRESS> 7eEd </SOURCE-START-ADDRESS>
                    <READ-DIAG-COMM-CONNECTOR>
                      <READ-PARAM-VALUES>
                        <READ-PARAM-VALUE SEMANTIC="assessing">
                          <PHYS-CONSTANT-VALUE> a &lt; b </PHYS-CONSTANT-VALUE>
                          <IN-PARAM-IF-SNREF SHORT-NAME="happiness_level" />
                        </READ-PARAM-VALUE>
                      </READ-PARAM-VALUES>
                      <READ-DIAG-COMM-REF ID-REF="somersault.service.report_status" DOCREF="somersault" DOCTYPE="CONTAINER" />
                      <READ-DATA-SNREF SHORT-NAME="happiness_level" />
                    </READ-DIAG-COMM-CONNECTOR>
                    <WRITE-DIAG-COMM-CONNECTOR>
                      <WRITE-DIAG-COMM-REF ID-REF="somersault.service.set_operation_params" DOCREF="somersault" DOCTYPE="CONTAINER" />
                      <WRITE-DATA-SNREF SHORT-NAME="use_fire_ring" />
                    </WRITE-DIAG-COMM-CONNECTOR>
                  </DIAG-COMM-DATA-CONNECTOR>
                </DIAG-COMM-DATA-CONNECTORS>
                <CONFIG-ID TYPE="A_ASCIISTRING"> this is identicating </CONFIG-ID>
                <DATA-RECORDS>
                  <DATA-RECORD DATAFORMAT="INTEL-HEX">
                    <SHORT-NAME>my_data_record</SHORT-NAME>
                    <RULE>one to rule them &lt;ll! </RULE>
                    <KEY> The key does not fit! </KEY>
                    <DATA-ID TYPE="A_BYTEFIELD">001122aBCd</DATA-ID>
                    <DATA>:020000020001fb
  :0500000068656C6C6FE7  
  
  :080005002C20776F726C64215E
  :04000005ABCDEF018f
:00000001FF


                    </DATA>
                  </DATA-RECORD>
                  <DATA-RECORD DATAFORMAT="BINARY">
                    <SHORT-NAME>my_binary_data_record</SHORT-NAME>
                    <RULE>yeah </RULE>
                    <KEY> dude! </KEY>
                    <DATA-ID TYPE="A_BYTEFIELD">112233bCDe</DATA-ID>
                    <DATA>

                    0002
   
                    abCd


</DATA>
                  </DATA-RECORD>
                  <DATA-RECORD DATAFORMAT="MOTOROLA-S">
                    <SHORT-NAME>my_moto_s_data_record</SHORT-NAME>
                    <RULE>schizophrenia</RULE>
                    <KEY> crowbar </KEY>
                    <DATA-ID TYPE="A_BYTEFIELD"></DATA-ID>
                    <DATA>

  S00F000068656C6C6F202020202000003C
 
     S11F00007C0802A6900100049421FFF07C6C1B787C8C23783C6000003863000026  

     S705ABCDEF0192  

                    </DATA>
                  </DATA-RECORD>
                </DATA-RECORDS>
                <AUDIENCE IS-DEVELOPMENT="true">
                </AUDIENCE>
                <SYSTEM-ITEMS>
                  <SYSTEM-ITEM SYSPARAM="time">
                    <SHORT-NAME>sysitem0</SHORT-NAME>
                    <BYTE-POSITION> 0 </BYTE-POSITION>
                    <DATA-OBJECT-PROP-REF ID-REF="ect.dop.wroom" />
                  </SYSTEM-ITEM>
                </SYSTEM-ITEMS>
                <DATA-ID-ITEM>
                  <SHORT-NAME>diditem</SHORT-NAME>
                  <BYTE-POSITION> 1 </BYTE-POSITION>
                  <DATA-OBJECT-PROP-REF ID-REF="somersault.DOP.uint16" DOCREF="somersault" DOCTYPE="CONTAINER" />
                </DATA-ID-ITEM>
                <OPTION-ITEMS>
                  <OPTION-ITEM>
                    <SHORT-NAME>optionitem0</SHORT-NAME>
                    <BYTE-POSITION> 2 </BYTE-POSITION>
                    <DATA-OBJECT-PROP-REF ID-REF="somersault.DOP.uint8" DOCREF="somersault" DOCTYPE="CONTAINER" />
                    <PHYSICAL-DEFAULT-VALUE> i am *not* an integer </PHYSICAL-DEFAULT-VALUE>
                    <ITEM-VALUES>
                      <ITEM-VALUE>
                        <PHYS-CONSTANT-VALUE> also not an integer </PHYS-CONSTANT-VALUE>
                        <MEANING TI="garbage">what do I mean?</MEANING>
                        <KEY>it may fit</KEY>
                        <RULE>one for them all</RULE>
                        <DESCRIPTION TI="literature">war and peace</DESCRIPTION>
                        <AUDIENCE IS-AFTERMARKET="true">
                        </AUDIENCE>
                      </ITEM-VALUE>
                    </ITEM-VALUES>
                    <WRITE-AUDIENCE IS-MANUFACTURING="true">
                    </WRITE-AUDIENCE>
                    <READ-AUDIENCE IS-AFTERMARKET="true">
                    </READ-AUDIENCE>
                  </OPTION-ITEM>
                </OPTION-ITEMS>
                <DEFAULT-DATA-RECORD-SNREF SHORT-NAME="dang" />
              </CONFIG-RECORD>
            </CONFIG-RECORDS>
          </CONFIG-DATA>
        </CONFIG-DATAS>
        <ADDITIONAL-AUDIENCES>
          <ADDITIONAL-AUDIENCE ID="ect_config_data0.aa.my_homies">
            <SHORT-NAME>my_homies</SHORT-NAME>
          </ADDITIONAL-AUDIENCE>
        </ADDITIONAL-AUDIENCES>
        <CONFIG-DATA-DICTIONARY-SPEC>
          <DATA-OBJECT-PROPS>
            <DATA-OBJECT-PROP ID="ect.dop.wroom">
              <SHORT-NAME>wroom</SHORT-NAME>
              <COMPU-METHOD>
                <CATEGORY>IDENTICAL</CATEGORY>
              </COMPU-METHOD>
              <DIAG-CODED-TYPE BASE-DATA-TYPE="A_UINT32" BASE-TYPE-ENCODING="NONE" xsi:type="STANDARD-LENGTH-TYPE">
                <BIT-LENGTH>5</BIT-LENGTH>
              </DIAG-CODED-TYPE>
              <PHYSICAL-TYPE BASE-DATA-TYPE="A_UINT32"/>
            </DATA-OBJECT-PROP>
          </DATA-OBJECT-PROPS>
          <UNIT-SPEC>
            <UNITS>
              <UNIT ID="ect.unit.pop">
                <SHORT-NAME>pop</SHORT-NAME>
                <DISPLAY-NAME>poops</DISPLAY-NAME>
              </UNIT>
            </UNITS>
          </UNIT-SPEC>
        </CONFIG-DATA-DICTIONARY-SPEC>
      </ECU-CONFIG>
    </ODX>"""

ecu_config_et = ElementTree.fromstring(ecu_config_xml_str)


def test_create_ecu_config_from_et() -> None:
    somersault_db._ecu_configs = NamedItemList()
    somersault_db.add_xml_tree(ecu_config_et)
    somersault_db.refresh()
    assert len(somersault_db.ecu_configs) == 1

    ecu_config = somersault_db.ecu_configs.ecu_config_test
    assert len(ecu_config._build_odxlinks()) == 4

    assert len(ecu_config.config_datas) == 1
    config_data = ecu_config.config_datas.ect_config_data0

    assert len(config_data.valid_base_variants) == 1
    valid_bv = config_data.valid_base_variants[0]
    assert len(valid_bv.ecu_variant_snrefs) == 1
    assert valid_bv.base_variant.short_name == "somersault_base_variant"

    assert len(config_data.config_records) == 1
    config_record = config_data.config_records.my_config_record
    config_id_item = config_record.config_id_item
    assert config_id_item is not None
    assert config_id_item.short_name == "my_config_id"
    assert config_id_item.byte_position == 123
    assert config_id_item.bit_position == 2
    assert config_id_item.data_object_prop.short_name == "temperature"

    assert len(config_record.diag_comm_data_connectors) == 1
    dcd_conn = config_record.diag_comm_data_connectors[0]
    assert dcd_conn.uncompressed_size == 432
    assert dcd_conn.source_start_address == 0x7eed

    rdcc = dcd_conn.read_diag_comm_connector
    assert rdcc is not None
    assert len(rdcc.read_param_values) == 1
    rpv = rdcc.read_param_values[0]
    assert rpv.semantic == "assessing"
    assert rpv.phys_constant_value == " a < b "
    assert rpv.in_param_if_snref == "happiness_level"
    assert rdcc.read_diag_comm is not None
    assert rdcc.read_diag_comm.short_name == "report_status"
    assert rdcc.read_data_snref == "happiness_level"

    wdcc = dcd_conn.write_diag_comm_connector
    assert wdcc is not None
    assert wdcc.write_diag_comm is not None
    assert wdcc.write_diag_comm.short_name == "set_operation_params"
    assert wdcc.write_data is not None
    assert wdcc.write_data.short_name == "use_fire_ring"

    assert config_record.config_id is not None
    assert config_record.config_id.value_type.value == "A_ASCIISTRING"
    assert config_record.config_id.value_raw == " this is identicating "

    assert len(config_record.data_records) == 3
    dr = config_record.data_records.my_data_record
    assert dr.rule == "one to rule them <ll! "
    assert dr.key == " The key does not fit! "
    assert dr.data_id is not None
    assert dr.data_id.value_type.value == "A_BYTEFIELD"
    assert dr.data_id.value_raw == "001122aBCd"
    assert dr.data_id.value == bytes.fromhex("001122aBCd")
    dset = dr.dataset
    assert isinstance(dset, BinFile)
    assert dset.execution_start_address == 0xabcdef01

    dr = config_record.data_records.my_binary_data_record
    dset_bin = dr.dataset
    assert isinstance(dset_bin, bytearray)
    assert dset_bin == b'\x00\x02\xab\xcd'
    assert dr.blob == b'\x00\x02\xab\xcd'

    dr = config_record.data_records.my_moto_s_data_record
    dset_moto = dr.dataset
    assert isinstance(dset_moto, BinFile)
    assert dset_moto.execution_start_address == 0xabcdef01

    assert config_record.audience is not None
    assert config_record.audience.is_development is True

    assert len(config_record.system_items) == 1
    si = config_record.system_items.sysitem0
    assert si.byte_position == 0
    assert si.data_object_prop.short_name == "wroom"

    dii = config_record.data_id_item
    assert dii is not None
    assert dii.short_name == "diditem"
    assert dii.data_object_prop.short_name == "uint16"

    assert len(config_record.option_items) == 1
    oi = config_record.option_items.optionitem0
    assert oi.byte_position == 2
    assert oi.data_object_prop.short_name == "uint8"
    assert oi.physical_default_value == " i am *not* an integer "

    assert len(oi.item_values) == 1
    iv = oi.item_values[0]
    assert iv.phys_constant_value == " also not an integer "
    assert str(iv.meaning) == "what do I mean?"
    assert iv.meaning is not None
    assert iv.meaning.text_identifier == "garbage"
    assert iv.key == "it may fit"
    assert iv.rule == "one for them all"
    assert str(iv.description) == "war and peace"
    assert iv.description is not None
    assert iv.description.text_identifier == "literature"
    assert iv.audience is not None
    assert iv.audience.is_aftermarket is True

    assert len(ecu_config.additional_audiences) == 1
    _ = ecu_config.additional_audiences.my_homies

    cdds = ecu_config.config_data_dictionary_spec
    assert cdds is not None
    assert len(cdds.data_object_props) == 1

    assert cdds.unit_spec is not None
    assert len(cdds.unit_spec.units) == 1


def test_write_ecu_config() -> None:
    somersault_db._ecu_configs = NamedItemList()
    somersault_db.add_xml_tree(ecu_config_et)
    somersault_db.refresh()
    assert len(somersault_db.ecu_configs) == 1

    __module_filename = inspect.getsourcefile(odxtools)
    assert isinstance(__module_filename, str)
    test_jinja_vars: dict[str, Any] = {}
    test_jinja_vars["ecu_config"] = somersault_db.ecu_configs[0]
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

    template = jinja_env.get_template("ecu_config.odx-e.xml.jinja2")
    rawodx: str = template.render(test_jinja_vars)

    rawodx2 = '\n'.join(rawodx.split("\n")[0:1] + rawodx.split("\n")[2:])
    expected_xml = ecu_config_xml_str.replace(" ", "").upper()
    actual_xml = rawodx2.replace(" ", "").upper()

    assert expected_xml == actual_xml
