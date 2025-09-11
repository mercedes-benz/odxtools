# SPDX-License-Identifier: MIT
import unittest

from odxtools.loadfile import load_pdx_file
from odxtools.parameters.valueparameter import ValueParameter


class TestWeakRef(unittest.TestCase):

    def test_weakref(self) -> None:
        # load PDX file whilst using weak references (non-refcounted) for
        # objects linked via ODXLINK or SNREF
        odxdb = load_pdx_file("./examples/somersault.pdx", use_weakrefs=True)

        service = odxdb.ecu_variants.somersault_lazy.services.session_start
        param = service.positive_responses.session.parameters.can_do_backward_flips
        assert isinstance(param, ValueParameter)

        self.assertEqual(param.dop.short_name, "boolean")

        # after deleting the database all objects referenced by param
        # via ODXLINK are immediately deleted because we use weak references
        # (which do not participate in reference counting).
        del odxdb

        with self.assertRaises(ReferenceError):
            self.assertEqual(param.dop.short_name, "boolean")

        # test that weak references are used by default
        odxdb = load_pdx_file("./examples/somersault.pdx")

        service = odxdb.ecu_variants.somersault_lazy.services.session_start
        param = service.positive_responses.session.parameters.can_do_backward_flips
        assert isinstance(param, ValueParameter)

        self.assertEqual(param.dop.short_name, "boolean")

        # after deleting the database all objects referenced by param
        # via ODXLINK are immediately deleted because we use weak references
        # (which do not participate in reference counting).
        del odxdb

        with self.assertRaises(ReferenceError):
            self.assertEqual(param.dop.short_name, "boolean")

    def test_normalref(self) -> None:
        # load PDX file whilst using reference counted references for
        # objects linked via ODXLINK or SNREF
        odxdb = load_pdx_file("./examples/somersault.pdx", use_weakrefs=False)

        service = odxdb.ecu_variants.somersault_lazy.services.session_start
        param = service.positive_responses.session.parameters.can_do_backward_flips
        assert isinstance(param, ValueParameter)

        self.assertEqual(param.dop.short_name, "boolean")

        # after deleting the database, objects referenced by param are
        # *not* deleted because we use normal references
        del odxdb

        self.assertEqual(param.dop.short_name, "boolean")


if __name__ == "__main__":
    unittest.main()
