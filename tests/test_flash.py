# SPDX-License-Identifier: MIT
import inspect
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import jinja2

import odxtools
from examples.somersaultecu import database as somersault_db
from odxtools.addrdeffilter import AddrdefFilter
from odxtools.addrdefphyssegment import AddrdefPhysSegment
from odxtools.exceptions import odxrequire
from odxtools.externflashdata import ExternFlashdata
from odxtools.internflashdata import InternFlashdata
from odxtools.nameditemlist import NamedItemList
from odxtools.negoffset import NegOffset
from odxtools.odxlink import DocType, OdxDocFragment
from odxtools.sizedeffilter import SizedefFilter
from odxtools.sizedefphyssegment import SizedefPhysSegment
from odxtools.writepdxfile import (jinja2_odxraise_helper, make_bool_xml_attrib, make_ref_attribs,
                                   make_xml_attrib, set_category_docfrag, set_layer_docfrag)

doc_frags = (OdxDocFragment(doc_name="flashtest", doc_type=DocType.FLASH),)

flash_xml_str = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <ODX MODEL-VERSION="2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="odx.xsd">
      <FLASH ID="odx.flash">
        <SHORT-NAME>flashtest</SHORT-NAME>
        <ECU-MEMS>
          <ECU-MEM ID="ecu_mems.my_ecu_mem">
            <SHORT-NAME>my_ecu_mem</SHORT-NAME>
            <MEM>
              <SESSIONS>
                <SESSION ID="sessions.my_session">
                  <SHORT-NAME>my_session</SHORT-NAME>
                  <EXPECTED-IDENTS>
                    <EXPECTED-IDENT ID="idents.foo">
                      <SHORT-NAME>foo</SHORT-NAME>
                      <IDENT-VALUES>
                        <IDENT-VALUE TYPE="A_ASCIISTRING">foo</IDENT-VALUE>
                      </IDENT-VALUES>
                    </EXPECTED-IDENT>
                  </EXPECTED-IDENTS>
                  <CHECKSUMS>
                    <CHECKSUM ID="checksum.blabb">
                      <SHORT-NAME>blabb</SHORT-NAME>
                      <FILLBYTE>  aB </FILLBYTE>
                      <SOURCE-START-ADDRESS> CdeF </SOURCE-START-ADDRESS>
                      <COMPRESSED-SIZE>  123  </COMPRESSED-SIZE>
                      <CHECKSUM-ALG>ODXTOOLS-SCRAMBLED-EGGS</CHECKSUM-ALG>
                      <UNCOMPRESSED-SIZE>1234</UNCOMPRESSED-SIZE>
                      <CHECKSUM-RESULT TYPE="A_ASCIISTRING">bar</CHECKSUM-RESULT>
                    </CHECKSUM>
                  </CHECKSUMS>
                  <SECURITYS>
                    <SECURITY>
                      <SECURITY-METHOD TYPE="A_ASCIISTRING">foobar</SECURITY-METHOD>
                      <FW-SIGNATURE TYPE="A_ASCIISTRING">baz</FW-SIGNATURE>
                      <FW-CHECKSUM TYPE="A_ASCIISTRING">qux</FW-CHECKSUM>
                      <VALIDITY-FOR TYPE="A_ASCIISTRING">quux</VALIDITY-FOR>
                    </SECURITY>
                  </SECURITYS>
                  <DATABLOCK-REFS>
                    <DATABLOCK-REF ID-REF="datablocks.shrubb" />
                  </DATABLOCK-REFS>
                </SESSION>
              </SESSIONS>
              <DATABLOCKS>
                <DATABLOCK ID="datablocks.shrubb" TYPE="my datablock">
                  <SHORT-NAME>shrubb</SHORT-NAME>
                  <LOGICAL-BLOCK-INDEX> 4a </LOGICAL-BLOCK-INDEX>
                  <FLASHDATA-REF ID-REF="flashdata.shrabb" />
                  <FILTERS>
                    <FILTER xsi:type="ADDRDEF-FILTER">
                      <FILTER-START>  42dB </FILTER-START>
                      <FILTER-END> 53eF </FILTER-END>
                    </FILTER>
                    <FILTER xsi:type="SIZEDEF-FILTER">
                      <FILTER-START> 42dE </FILTER-START>
                      <FILTER-SIZE>  423 </FILTER-SIZE>
                    </FILTER>
                  </FILTERS>
                  <SEGMENTS>
                    <SEGMENT ID="segments.my_segment">
                      <SHORT-NAME>my_segment</SHORT-NAME>
                      <SOURCE-START-ADDRESS> B005  </SOURCE-START-ADDRESS>
                      <COMPRESSED-SIZE> 123 </COMPRESSED-SIZE>
                      <UNCOMPRESSED-SIZE> 12345  </UNCOMPRESSED-SIZE>
                      <ENCRYPT-COMPRESS-METHOD TYPE="A_BYTEFIELD"> b7ac7507e0 </ENCRYPT-COMPRESS-METHOD>
                    </SEGMENT>
                  </SEGMENTS>
                  <TARGET-ADDR-OFFSET xsi:type="NEG-OFFSET">
                    <NEGATIVE-OFFSET>  6ab9 </NEGATIVE-OFFSET>
                  </TARGET-ADDR-OFFSET>
                  <OWN-IDENTS>
                    <OWN-IDENT ID="idents.holla">
                      <SHORT-NAME>holla</SHORT-NAME>
                      <IDENT-VALUE TYPE="A_ASCIISTRING">blabertrash</IDENT-VALUE>
                    </OWN-IDENT>
                  </OWN-IDENTS>
                  <SECURITYS>
                    <SECURITY>
                      <SECURITY-METHOD TYPE="A_BYTEFIELD">00aB</SECURITY-METHOD>
                      <FW-SIGNATURE TYPE="A_BYTEFIELD">01cD</FW-SIGNATURE>
                      <FW-CHECKSUM TYPE="A_BYTEFIELD">03eF</FW-CHECKSUM>
                      <VALIDITY-FOR TYPE="A_BYTEFIELD">04Ab</VALIDITY-FOR>
                    </SECURITY>
                  </SECURITYS>
                </DATABLOCK>
              </DATABLOCKS>
              <FLASHDATAS>
                <FLASHDATA ID="flashdata.shrabb" xsi:type="EXTERN-FLASHDATA">
                  <SHORT-NAME>shrabb</SHORT-NAME>
                  <SIZE-LENGTH>  42242 </SIZE-LENGTH>
                  <ADDRESS-LENGTH>  52252 </ADDRESS-LENGTH>
                  <DATAFORMAT SELECTION="USER-DEFINED" USER-SELECTION="&gt; hello" />
                  <DATAFILE LATEBOUND-DATAFILE="false">my_funny_blob.hex</DATAFILE>
                </FLASHDATA>
                <FLASHDATA ID="flashdata.shrobb" xsi:type="INTERN-FLASHDATA">
                  <SHORT-NAME>shrobb</SHORT-NAME>
                  <SIZE-LENGTH>  31141 </SIZE-LENGTH>
                  <ADDRESS-LENGTH>  41141 </ADDRESS-LENGTH>
                  <DATAFORMAT SELECTION="USER-DEFINED" USER-SELECTION="&lt; world" />
                  <DATA>this is the stuff that gets shoved to the ECU as its firmware</DATA>
                </FLASHDATA>
              </FLASHDATAS>
            </MEM>
            <PHYS-MEM ID="phys_mems.my_phys_mem">
              <SHORT-NAME>my_phys_mem</SHORT-NAME>
              <PHYS-SEGMENTS>
                <PHYS-SEGMENT ID="phys_segments.my_sizedefdef_phys_segment" xsi:type="SIZEDEF-PHYS-SEGMENT">
                  <SHORT-NAME>my_sizedefdef_phys_segment</SHORT-NAME>
                  <FILLBYTE>  cC </FILLBYTE>
                  <BLOCK-SIZE>  825 </BLOCK-SIZE>
                  <START-ADDRESS>  F00b </START-ADDRESS>
                  <SIZE>  101 </SIZE>
                </PHYS-SEGMENT>
                <PHYS-SEGMENT ID="phys_segments.my_addrdef_phys_segment" xsi:type="ADDRDEF-PHYS-SEGMENT">
                  <SHORT-NAME>my_addrdef_phys_segment</SHORT-NAME>
                  <FILLBYTE>  bB </FILLBYTE>
                  <BLOCK-SIZE>  714 </BLOCK-SIZE>
                  <START-ADDRESS>  EFFa </START-ADDRESS>
                  <END-ADDRESS> 1000 </END-ADDRESS>
                </PHYS-SEGMENT>
              </PHYS-SEGMENTS>
            </PHYS-MEM>
          </ECU-MEM>
        </ECU-MEMS>
        <ECU-MEM-CONNECTORS>
          <ECU-MEM-CONNECTOR ID="ecu_mem_connectors.my_connector">
            <SHORT-NAME>my_ecu_mem_connector</SHORT-NAME>
            <FLASH-CLASSS>
              <FLASH-CLASS ID="flash_classes.my_flash_class">
                <SHORT-NAME>my_flash_class</SHORT-NAME>
              </FLASH-CLASS>
            </FLASH-CLASSS>
            <SESSION-DESCS>
              <SESSION-DESC DIRECTION="UPLOAD">
                <SHORT-NAME>my_session_desc</SHORT-NAME>
                <PARTNUMBER>ABC123</PARTNUMBER>
                <PRIORITY> 5 </PRIORITY>
                <SESSION-SNREF SHORT-NAME="session_NA" />
                <DIAG-COMM-SNREF SHORT-NAME="diag_comm_NA" />
                <FLASH-CLASS-REFS>
                  <FLASH-CLASS-REF ID-REF="flash_classes.my_flash_class" />
                </FLASH-CLASS-REFS>
                <OWN-IDENT ID="own_idents.my_own_ident">
                  <SHORT-NAME>my_own_ident</SHORT-NAME>
                  <IDENT-VALUE TYPE="A_ASCIISTRING">own identValue</IDENT-VALUE>
                </OWN-IDENT>
              </SESSION-DESC>
            </SESSION-DESCS>
            <IDENT-DESCS>
              <IDENT-DESC>
                <DIAG-COMM-SNREF SHORT-NAME="diag_comm_NA" />
                <IDENT-IF-SNREF SHORT-NAME="ident_if_NA" />
                <OUT-PARAM-IF-SNREF SHORT-NAME="out_param_if_NA" />
              </IDENT-DESC>
            </IDENT-DESCS>
            <ECU-MEM-REF ID-REF="ecu_mems.my_ecu_mem" />
            <LAYER-REFS>
              <LAYER-REF ID-REF="somersault_lazy" DOCREF="somersault" DOCTYPE="CONTAINER" />
            </LAYER-REFS>
            <ALL-VARIANT-REFS>
              <ALL-VARIANT-REF ID-REF="somersault.base_variant"  DOCREF="somersault" DOCTYPE="CONTAINER" />
            </ALL-VARIANT-REFS>
          </ECU-MEM-CONNECTOR>
        </ECU-MEM-CONNECTORS>
        <ADDITIONAL-AUDIENCES>
          <ADDITIONAL-AUDIENCE ID="additional_audiences.hacker">
            <SHORT-NAME>hacker</SHORT-NAME>
          </ADDITIONAL-AUDIENCE>
        </ADDITIONAL-AUDIENCES>
      </FLASH>
    </ODX>"""

flash_et = ElementTree.fromstring(flash_xml_str)


def test_create_flash_from_et() -> None:
    somersault_db._flashs = NamedItemList()
    somersault_db.add_xml_tree(flash_et)
    somersault_db.add_auxiliary_file("my_funny_blob.hex", BytesIO(b"I can do whatever I want"))
    somersault_db.refresh()
    assert len(somersault_db.flashs) == 1

    flash = somersault_db.flashs.flashtest
    assert len(flash._build_odxlinks()) == 17

    assert len(flash.ecu_mems) == 1
    ecu_mem = flash.ecu_mems.my_ecu_mem
    assert len(ecu_mem.mem.sessions) == 1

    session = ecu_mem.mem.sessions.my_session
    assert len(session.expected_idents) == 1
    eid = session.expected_idents.foo
    assert len(eid.ident_values) == 1
    assert eid.ident_values[0].value_type.value == "A_ASCIISTRING"
    assert eid.ident_values[0].value == "foo"

    assert len(session.checksums) == 1
    checksum = session.checksums.blabb
    assert checksum.fillbyte == 0xab
    assert checksum.source_start_address == 0xcdef
    assert checksum.checksum_alg == "ODXTOOLS-SCRAMBLED-EGGS"

    assert len(session.securities) == 1
    security = session.securities[0]
    assert odxrequire(security.security_method).value_type.value == "A_ASCIISTRING"
    assert odxrequire(security.security_method).value == "foobar"
    assert odxrequire(security.fw_signature).value == "baz"
    assert odxrequire(security.fw_checksum).value == "qux"
    assert odxrequire(security.validity_for).value == "quux"

    assert len(session.datablock_refs) == 1
    assert len(session.datablocks) == 1
    assert session.datablocks[0].short_name == "shrubb"

    assert len(ecu_mem.mem.datablocks) == 1
    datablock = ecu_mem.mem.datablocks.shrubb
    assert datablock.logical_block_index == 0x4a
    assert odxrequire(datablock.flashdata).short_name == "shrabb"
    assert len(datablock.filters) == 2
    assert isinstance(datablock.filters[0], AddrdefFilter)
    assert isinstance(datablock.filters[1], SizedefFilter)
    assert datablock.filters[0].filter_start == 0x42db
    assert datablock.filters[0].filter_end == 0x53ef
    assert datablock.filters[1].filter_start == 0x42de
    assert datablock.filters[1].filter_size == 423

    assert len(datablock.securities) == 1
    security = datablock.securities[0]
    assert odxrequire(security.security_method).value_type.value == "A_BYTEFIELD"
    assert odxrequire(security.security_method).value_raw == "00aB"
    assert odxrequire(security.security_method).value == bytes.fromhex("00aB")
    assert odxrequire(security.fw_signature).value_type.value == "A_BYTEFIELD"
    assert odxrequire(security.fw_signature).value_raw == "01cD"
    assert odxrequire(security.fw_signature).value == bytes.fromhex("01cD")
    assert odxrequire(security.fw_checksum).value_type.value == "A_BYTEFIELD"
    assert odxrequire(security.fw_checksum).value_raw == "03eF"
    assert odxrequire(security.fw_checksum).value == bytes.fromhex("03eF")
    assert odxrequire(security.validity_for).value_type.value == "A_BYTEFIELD"
    assert odxrequire(security.validity_for).value_raw == "04Ab"
    assert odxrequire(security.validity_for).value == bytes.fromhex("04Ab")

    assert len(datablock.segments) == 1
    segment = datablock.segments.my_segment
    assert segment.source_start_address == 0xb005
    assert segment.compressed_size == 123
    assert segment.uncompressed_size == 12345
    assert odxrequire(segment.encrypt_compress_method).value_type.value == "A_BYTEFIELD"
    assert odxrequire(segment.encrypt_compress_method).value_raw.strip() == "b7ac7507e0"
    assert odxrequire(segment.encrypt_compress_method).value == bytes.fromhex("b7ac7507e0")

    tao = odxrequire(datablock.target_addr_offset)
    assert isinstance(tao, NegOffset)
    assert tao.negative_offset == 0x6ab9
    assert len(datablock.own_idents) == 1
    own_ident = datablock.own_idents.holla
    assert own_ident.ident_value.value_type.value == "A_ASCIISTRING"
    assert own_ident.ident_value.value == "blabertrash"

    assert len(ecu_mem.mem.flashdatas) == 2
    flashdata = ecu_mem.mem.flashdatas.shrabb
    assert isinstance(flashdata, ExternFlashdata)
    assert flashdata.size_length == 42242
    assert flashdata.address_length == 52252
    assert flashdata.dataformat.selection.value == "USER-DEFINED"
    assert flashdata.dataformat.user_selection == "> hello"
    assert flashdata.datafile.latebound_datafile is False
    assert flashdata.datafile.value == "my_funny_blob.hex"

    flashdata = ecu_mem.mem.flashdatas.shrobb
    assert isinstance(flashdata, InternFlashdata)
    assert flashdata.size_length == 31141
    assert flashdata.address_length == 41141
    assert flashdata.dataformat.selection.value == "USER-DEFINED"
    assert flashdata.dataformat.user_selection == "< world"
    assert flashdata.data == "this is the stuff that gets shoved to the ECU as its firmware"

    phys_mem = odxrequire(ecu_mem.phys_mem)
    assert phys_mem.short_name == "my_phys_mem"

    assert len(phys_mem.phys_segments) == 2
    phys_segment = phys_mem.phys_segments.my_sizedefdef_phys_segment
    assert isinstance(phys_segment, SizedefPhysSegment)
    assert phys_segment.fillbyte == 0xcc
    assert phys_segment.block_size == 825
    assert phys_segment.start_address == 0xf00b
    assert phys_segment.size == 101

    phys_segment = phys_mem.phys_segments.my_addrdef_phys_segment
    assert isinstance(phys_segment, AddrdefPhysSegment)


def test_write_flash() -> None:
    somersault_db._flashs = NamedItemList()
    somersault_db.add_xml_tree(flash_et)
    somersault_db.refresh()
    assert len(somersault_db.flashs) == 1

    __module_filename = inspect.getsourcefile(odxtools)
    assert isinstance(__module_filename, str)
    test_jinja_vars: dict[str, Any] = {}
    test_jinja_vars["flash"] = somersault_db.flashs[0]
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

    template = jinja_env.get_template("flash.odx-f.xml.jinja2")
    rawodx: str = template.render(test_jinja_vars)

    rawodx2 = '\n'.join(rawodx.split("\n")[0:1] + rawodx.split("\n")[2:])
    expected_xml = flash_xml_str.replace(" ", "").upper()
    actual_xml = rawodx2.replace(" ", "").upper()

    assert expected_xml == actual_xml
