# SPDX-License-Identifier: MIT
"""Consistency checks over a loaded database."""
import argparse
import contextlib
import io
import unittest
from unittest import mock

import odxtools
from odxtools.checks import RULES, Finding, Severity, run_checks
from odxtools.checks.overlapping_parameters import _bit_span, _overlaps_in
from odxtools.cli import _parser_utils
from odxtools.cli import check as check_tool


class _Param:
    """A parameter placed at a known position, which is all the rule looks at."""

    def __init__(self,
                 short_name: str,
                 byte_position: int | None,
                 bit_length: int | None,
                 bit_position: int | None = None) -> None:
        self.short_name = short_name
        self.byte_position = byte_position
        self.bit_position = bit_position
        self._bit_length = bit_length

    def get_static_bit_length(self) -> int | None:
        return self._bit_length


class _Codec:
    """Minimal stand-in for anything carrying parameters."""

    def __init__(self, *parameters: _Param) -> None:
        self.short_name = "codec"
        self.parameters = list(parameters)


class TestBitSpan(unittest.TestCase):

    def test_position_and_length_give_a_span(self) -> None:
        self.assertEqual(_bit_span(_Param("p", 2, 16)), (16, 32))  # type: ignore[arg-type]

    def test_bit_position_shifts_the_span(self) -> None:
        self.assertEqual(
            _bit_span(_Param("p", 1, 4, bit_position=2)),  # type: ignore[arg-type]
            (10, 14))

    def test_a_parameter_without_a_position_cannot_be_placed(self) -> None:
        """Such a parameter follows whatever precedes it."""
        self.assertIsNone(_bit_span(_Param("p", None, 8)))  # type: ignore[arg-type]

    def test_a_parameter_without_a_static_length_cannot_be_placed(self) -> None:
        """Its length is decided by the data it carries."""
        self.assertIsNone(_bit_span(_Param("p", 0, None)))  # type: ignore[arg-type]


class TestOverlapDetection(unittest.TestCase):

    def test_adjacent_parameters_do_not_overlap(self) -> None:
        codec = _Codec(_Param("first", 0, 8), _Param("second", 1, 8))

        self.assertEqual(list(_overlaps_in(codec)), [])  # type: ignore[arg-type]

    def test_parameters_on_the_same_bytes_overlap(self) -> None:
        codec = _Codec(_Param("first", 1, 16), _Param("second", 1, 16))

        found = list(_overlaps_in(codec))  # type: ignore[arg-type]

        self.assertEqual(len(found), 1)
        self.assertEqual({p.short_name for p in found[0]}, {"first", "second"})

    def test_a_partial_overlap_is_reported(self) -> None:
        codec = _Codec(_Param("first", 0, 24), _Param("second", 2, 16))

        self.assertEqual(len(list(_overlaps_in(codec))), 1)  # type: ignore[arg-type]

    def test_unplaceable_parameters_are_passed_over(self) -> None:
        """Two parameters which cannot be placed cannot be said to overlap."""
        codec = _Codec(_Param("first", None, 8), _Param("second", None, 8))

        self.assertEqual(list(_overlaps_in(codec)), [])  # type: ignore[arg-type]


class TestReferenceDatabase(unittest.TestCase):

    def test_somersault_has_no_findings(self) -> None:
        """A conforming database must not be reported by any rule."""
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        self.assertEqual([str(f) for f in run_checks(odxdb)], [])


class TestFinding(unittest.TestCase):

    def test_str_names_severity_location_message_and_rule(self) -> None:
        finding = Finding(
            rule="a-rule",
            severity=Severity.ERROR,
            location=("Ecu", "Service"),
            message="something is wrong",
        )

        self.assertEqual(str(finding), "error: Ecu/Service: something is wrong [a-rule]")

    def test_registered_rules_are_named(self) -> None:
        self.assertTrue(RULES)
        for rule in RULES:
            self.assertTrue(rule.name)


class TestExitStatus(unittest.TestCase):
    """The exit status is what makes the tool usable in a pipeline."""

    def _run(self, findings: list[Finding], warnings_as_errors: bool = False) -> int:
        args = argparse.Namespace(pdx_file="unused", warnings_as_errors=warnings_as_errors)
        with mock.patch.object(_parser_utils, "load_file", return_value=object()), \
             mock.patch.object(check_tool, "run_checks", return_value=iter(findings)), \
             contextlib.redirect_stdout(io.StringIO()):
            try:
                check_tool.run(args)
            except SystemExit as exit_:
                return int(exit_.code or 0)
        return 0

    def test_no_findings_is_a_success(self) -> None:
        self.assertEqual(self._run([]), 0)

    def test_an_error_fails(self) -> None:
        self.assertEqual(self._run([_finding(Severity.ERROR)]), 1)

    def test_a_warning_alone_does_not_fail(self) -> None:
        self.assertEqual(self._run([_finding(Severity.WARNING)]), 0)

    def test_a_warning_fails_when_asked_for(self) -> None:
        self.assertEqual(self._run([_finding(Severity.WARNING)], warnings_as_errors=True), 1)


def _finding(severity: Severity) -> Finding:
    return Finding(rule="a-rule", severity=severity, location=("Ecu",), message="something")


if __name__ == "__main__":
    unittest.main()
