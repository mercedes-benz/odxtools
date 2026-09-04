# SPDX-License-Identifier: MIT
"""Diagnostics emitted when a reference points to the wrong kind of DOP.

The ODX standard only allows simple DOPs in a few places, e.g. for the value
of a PHYS-CONST parameter. When a file violates this, the message needs to
name the offending element so that it can be found in a large database.
"""
import unittest

import odxtools.exceptions as exceptions
from odxtools.exceptions import OdxError
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.parameters.physicalconstantparameter import PhysicalConstantParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.snrefcontext import SnRefContext
from odxtools.structure import Structure

doc_frags = (OdxDocFragment("test", DocType.CONTAINER),)


def _structure(short_name: str) -> Structure:
    return Structure(
        odx_id=OdxLinkId(short_name, doc_frags),
        short_name=short_name,
        parameters=NamedItemList(),
    )


class TestDopTypeDiagnostics(unittest.TestCase):

    def setUp(self) -> None:
        self.structure = _structure("a_structure")
        self.odxlinks = OdxLinkDatabase()
        self.odxlinks.update({self.structure.odx_id: self.structure})
        self.context = SnRefContext(use_weakrefs=False)

    def test_physical_constant_parameter_names_the_element(self) -> None:
        param = PhysicalConstantParameter(
            short_name="the_constant",
            physical_constant_value_raw="1",
            dop_ref=OdxLinkRef.from_id(self.structure.odx_id),
        )
        param._resolve_odxlinks(self.odxlinks)

        with self.assertRaises(OdxError) as ctx:
            param._resolve_snrefs(self.context)

        message = str(ctx.exception)
        self.assertIn("the_constant", message)
        self.assertIn("a_structure", message)
        self.assertIn("Structure", message)

    def test_value_parameter_names_the_element(self) -> None:
        param = ValueParameter(
            short_name="the_value",
            physical_default_value_raw="1",
            dop_ref=OdxLinkRef.from_id(self.structure.odx_id),
        )
        param._resolve_odxlinks(self.odxlinks)

        with self.assertRaises(OdxError) as ctx:
            param._resolve_snrefs(self.context)

        message = str(ctx.exception)
        self.assertIn("the_value", message)
        self.assertIn("a_structure", message)
        self.assertIn("Structure", message)

    def test_unresolved_reference_is_not_reported_as_a_wrong_type(self) -> None:
        """An unresolved DOP must read differently from one of the wrong type."""
        param = PhysicalConstantParameter(
            short_name="the_constant",
            physical_constant_value_raw="1",
            dop_ref=OdxLinkRef("does_not_exist", doc_frags),
        )

        exceptions.strict_mode = False
        try:
            param._resolve_odxlinks(OdxLinkDatabase())
        finally:
            exceptions.strict_mode = True

        self.assertIn("does_not_exist", param.dop_info)
        self.assertIn("unresolvable", param.dop_info)

    def test_description_names_the_reference_as_written(self) -> None:
        """The name in the message is the one the ODX file uses."""
        param = PhysicalConstantParameter(
            short_name="the_constant",
            physical_constant_value_raw="1",
            dop_ref=OdxLinkRef.from_id(self.structure.odx_id),
        )
        param._resolve_odxlinks(self.odxlinks)

        self.assertIn("a_structure", param.dop_info)
        self.assertIn("Structure", param.dop_info)


if __name__ == "__main__":
    unittest.main()
