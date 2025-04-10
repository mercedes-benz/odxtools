# SPDX-License-Identifier: MIT
from xml.etree import ElementTree

import pytest
from packaging.version import Version

from odxtools.basevariantpattern import BaseVariantPattern
from odxtools.ecuvariantpattern import EcuVariantPattern
from odxtools.exceptions import OdxError
from odxtools.odxdoccontext import OdxDocContext
from odxtools.odxlink import DocType, OdxDocFragment

doc_frags = (OdxDocFragment(doc_name="pytest", doc_type=DocType.CONTAINER),)


@pytest.fixture()
def valid_evp_et() -> ElementTree.Element:
    xml = """
    <ECU-VARIANT-PATTERNS>
        <ECU-VARIANT-PATTERN>
            <MATCHING-PARAMETERS>
                <MATCHING-PARAMETER>
                    <EXPECTED-VALUE>65535</EXPECTED-VALUE>
                    <DIAG-COMM-SNREF SHORT-NAME="IdentService"/>
                    <OUT-PARAM-IF-SNREF SHORT-NAME="Id"/>
                </MATCHING-PARAMETER>
            </MATCHING-PARAMETERS>
        </ECU-VARIANT-PATTERN>
        <ECU-VARIANT-PATTERN>
            <MATCHING-PARAMETERS>
                <MATCHING-PARAMETER>
                    <EXPECTED-VALUE>255</EXPECTED-VALUE>
                    <DIAG-COMM-SNREF SHORT-NAME="SerialNumber"/>
                    <OUT-PARAM-IF-SNREF SHORT-NAME="Value"/>
                </MATCHING-PARAMETER>
                <MATCHING-PARAMETER>
                    <EXPECTED-VALUE>supplier_A</EXPECTED-VALUE>
                    <DIAG-COMM-SNREF SHORT-NAME="SupplierInfo"/>
                    <OUT-PARAM-IF-SNPATHREF SHORT-NAME-PATH="name.english"/>
                </MATCHING-PARAMETER>
            </MATCHING-PARAMETERS>
        </ECU-VARIANT-PATTERN>
    </ECU-VARIANT-PATTERNS>
    """
    return ElementTree.fromstring(xml)


@pytest.fixture()
def valid_bvp_et() -> ElementTree.Element:
    xml = """
    <BASE-VARIANT-PATTERNS>
        <BASE-VARIANT-PATTERN>
            <MATCHING-BASE-VARIANT-PARAMETERS>
                <MATCHING-BASE-VARIANT-PARAMETER>
                    <EXPECTED-VALUE>1234</EXPECTED-VALUE>
                    <DIAG-COMM-SNREF SHORT-NAME="Identify"/>
                    <OUT-PARAM-IF-SNREF SHORT-NAME="ECU_ID"/>
                </MATCHING-BASE-VARIANT-PARAMETER>
            </MATCHING-BASE-VARIANT-PARAMETERS>
        </BASE-VARIANT-PATTERN>
        <BASE-VARIANT-PATTERN>
            <MATCHING-BASE-VARIANT-PARAMETERS>
                <MATCHING-BASE-VARIANT-PARAMETER>
                    <EXPECTED-VALUE>234</EXPECTED-VALUE>
                    <USE-PHYSICAL-ADDRESSING>true</USE-PHYSICAL-ADDRESSING>
                    <DIAG-COMM-SNREF SHORT-NAME="SerialInfo"/>
                    <OUT-PARAM-IF-SNREF SHORT-NAME="Val"/>
                </MATCHING-BASE-VARIANT-PARAMETER>
                <MATCHING-BASE-VARIANT-PARAMETER>
                    <EXPECTED-VALUE>OEM</EXPECTED-VALUE>
                    <USE-PHYSICAL-ADDRESSING>false</USE-PHYSICAL-ADDRESSING>
                    <DIAG-COMM-SNREF SHORT-NAME="ManufacturerInfo"/>
                    <OUT-PARAM-IF-SNPATHREF SHORT-NAME-PATH="info.type"/>
                </MATCHING-BASE-VARIANT-PARAMETER>
            </MATCHING-BASE-VARIANT-PARAMETERS>
        </BASE-VARIANT-PATTERN>
    </BASE-VARIANT-PATTERNS>
    """
    return ElementTree.fromstring(xml)


@pytest.fixture()
def invalid_evp_et() -> ElementTree.Element:
    xml = """
    <ECU-VARIANT-PATTERNS>
        <ECU-VARIANT-PATTERN>
            <MATCHING-PARAMETERS>
            </MATCHING-PARAMETERS>
        </ECU-VARIANT-PATTERN>
    </ECU-VARIANT-PATTERNS>
    """
    return ElementTree.fromstring(xml)


def test_create_bvp_from_et(valid_bvp_et: ElementTree.Element) -> None:
    base_variant_patterns = [
        BaseVariantPattern.from_et(elem, OdxDocContext(Version("2.2.0"), doc_frags))
        for elem in valid_bvp_et.iterfind("BASE-VARIANT-PATTERN")
    ]
    assert len(base_variant_patterns) == 2
    assert base_variant_patterns[0].matching_base_variant_parameters[0].use_physical_addressing
    assert base_variant_patterns[0].matching_base_variant_parameters[0].matches({"ECU_ID": 1234})
    assert base_variant_patterns[1].matching_base_variant_parameters[0].use_physical_addressing
    assert base_variant_patterns[1].matching_base_variant_parameters[0].matches({"Val": 234})
    assert not base_variant_patterns[1].matching_base_variant_parameters[1].use_physical_addressing
    assert base_variant_patterns[1].matching_base_variant_parameters[1].matches(
        {"info": {
            "type": "OEM"
        }})

    assert not base_variant_patterns[1].matching_base_variant_parameters[1].matches(
        {"info": {
            "type": 123
        }})

    assert not base_variant_patterns[1].matching_base_variant_parameters[1].matches(
        {"info": {
            "type": "scammer"
        }})

    assert not base_variant_patterns[1].matching_base_variant_parameters[1].matches(
        {"nice2know": {
            "type": "OEM"
        }})


def test_create_evp_from_et(valid_evp_et: ElementTree.Element) -> None:
    ecu_variant_patterns = [
        EcuVariantPattern.from_et(elem, OdxDocContext(Version("2.2.0"), doc_frags))
        for elem in valid_evp_et.iterfind("ECU-VARIANT-PATTERN")
    ]
    assert len(ecu_variant_patterns) == 2
    assert ecu_variant_patterns[0].matching_parameters[0].matches({"Id": 0xFFFF})
    assert ecu_variant_patterns[1].matching_parameters[0].matches({"Value": 0xFF})
    assert ecu_variant_patterns[1].matching_parameters[1].matches(
        {"name": {
            "english": "supplier_A"
        }})


def test_create_invalid_evp_from_et(invalid_evp_et: ElementTree.Element) -> None:
    with pytest.raises(OdxError):
        for x in invalid_evp_et.iterfind("ECU-VARIANT-PATTERN"):
            EcuVariantPattern.from_et(x, OdxDocContext(Version("2.2.0"), doc_frags))
