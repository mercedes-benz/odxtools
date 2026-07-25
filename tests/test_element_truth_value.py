# SPDX-License-Identifier: MIT
import unittest
import warnings
from xml.etree import ElementTree

from packaging.version import Version

from odxtools.dynamicendmarkerfield import DynamicEndmarkerField
from odxtools.odxdoccontext import OdxDocContext
from odxtools.odxlink import OdxDocFragment
from odxtools.subcomponentparamconnector import SubComponentParamConnector

doc_frags = (OdxDocFragment("UnitTest", "CONTAINER"),)
context = OdxDocContext(Version("2.2.0"), doc_frags)


class TestElementTruthValue(unittest.TestCase):
    """Elements must not be tested for truthiness (deprecated since 3.12)."""

    def test_sub_component_param_connector(self) -> None:
        et_element = ElementTree.fromstring("""
        <SUB-COMPONENT-PARAM-CONNECTOR ID="connector">
          <SHORT-NAME>connector</SHORT-NAME>
          <DIAG-COMM-SNREF SHORT-NAME="service"/>
          <OUT-PARAM-IF-REFS/>
          <IN-PARAM-IF-REFS>
            <IN-PARAM-IF-SNREF SHORT-NAME="param"/>
          </IN-PARAM-IF-REFS>
        </SUB-COMPONENT-PARAM-CONNECTOR>""")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            connector = SubComponentParamConnector.from_et(et_element, context)

        self.assertEqual([str(w.message) for w in caught], [])
        self.assertEqual(connector.out_param_if_refs, [])
        self.assertEqual(connector.in_param_if_refs, ["param"])

    def test_dynamic_endmarker_field(self) -> None:
        et_element = ElementTree.fromstring("""
        <DYNAMIC-ENDMARKER-FIELD ID="field">
          <SHORT-NAME>field</SHORT-NAME>
          <BASIC-STRUCTURE-REF ID-REF="structure"/>
          <DYN-END-DOP-REF ID-REF="dop">
            <TERMINATION-VALUE>0</TERMINATION-VALUE>
          </DYN-END-DOP-REF>
        </DYNAMIC-ENDMARKER-FIELD>""")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            field = DynamicEndmarkerField.from_et(et_element, context)

        self.assertEqual([str(w.message) for w in caught], [])
        self.assertEqual(field.dyn_end_dop_ref.ref_id, "dop")


if __name__ == "__main__":
    unittest.main()
