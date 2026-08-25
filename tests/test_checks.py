# SPDX-License-Identifier: MIT
import argparse
import itertools
import unittest
from dataclasses import dataclass
from typing import Any
from unittest import mock

import odxtools
from odxtools.checks import DEFAULT_RULES, Finding, Rule, Severity, run_checks
from odxtools.checks.nrc_const_without_value import NrcConstWithoutValue
from odxtools.checks.objects import iter_codecs, iter_objects
from odxtools.diagservice import DiagService
from odxtools.checks.overlapping_parameters import (OverlappingParameters, _bit_span, _overlaps,
                                                    _place)
from odxtools.cli import _parser_utils
from odxtools.cli import check as check_tool
from odxtools.parameters.nrcconstparameter import NrcConstParameter
from odxtools.parameters.valueparameter import ValueParameter


@dataclass
class _Param:
    short_name: str
    byte_position: int | None
    static_bit_length: int | None
    bit_position: int | None = None

    def get_static_bit_length(self) -> int | None:
        return self.static_bit_length


class _Codec:
    short_name = "codec"

    def __init__(self, parameters: list[Any]) -> None:
        self.parameters = parameters


def _fake(cls: type, byte_position: int | None, bit_length: int | None, name: str = "p") -> Any:
    """A parameter that is an actual instance of ``cls`` for isinstance checks."""
    param: Any = object.__new__(cls)
    object.__setattr__(param, "short_name", name)
    object.__setattr__(param, "byte_position", byte_position)
    object.__setattr__(param, "bit_position", None)
    object.__setattr__(param, "get_static_bit_length", lambda: bit_length)
    return param


class TestSeverity(unittest.TestCase):

    def test_levels_are_ordered_numbers(self) -> None:
        self.assertGreater(Severity.ERROR, Severity.WARNING)
        self.assertGreater(Severity.WARNING, Severity.INFO)
        self.assertGreater(Severity.INFO, Severity.DEBUG)

    def test_values_follow_the_logging_convention(self) -> None:
        self.assertEqual((Severity.DEBUG, Severity.INFO, Severity.WARNING, Severity.ERROR),
                         (10, 20, 30, 40))

    def test_filtering_by_threshold_is_a_comparison(self) -> None:
        """The point of numeric levels: 'info and above' is a single >=."""
        at_least_info = [s for s in Severity if s >= Severity.INFO]
        self.assertEqual(at_least_info, [Severity.INFO, Severity.WARNING, Severity.ERROR])


class TestFinding(unittest.TestCase):

    def test_str_prints_location_first_and_the_level_name(self) -> None:
        finding = Finding(
            rule="a-rule",
            severity=Severity.ERROR,
            location=("Ecu", "Service"),
            message="something is wrong")

        self.assertEqual(str(finding), "Ecu/Service: error: something is wrong [a-rule]")

    def test_str_never_prints_the_numeric_value(self) -> None:
        finding = Finding(rule="r", severity=Severity.ERROR, location=("Ecu",), message="m")

        self.assertNotIn("40", str(finding))

    def test_a_location_is_required(self) -> None:
        with self.assertRaises(TypeError):
            Finding(rule="r", severity=Severity.ERROR, message="m")  # type: ignore[call-arg]


class TestRuleRegistry(unittest.TestCase):

    def test_registered_rules_have_unique_names_and_a_spec(self) -> None:
        self.assertTrue(DEFAULT_RULES)
        names = [rule.name for rule in DEFAULT_RULES]
        self.assertEqual(len(names), len(set(names)))
        for rule in DEFAULT_RULES:
            self.assertTrue(rule.spec, f"rule '{rule.name}' does not say what it draws on")
            self.assertIsInstance(rule, Rule)


class TestBitSpan(unittest.TestCase):

    def test_a_positioned_parameter_is_placed(self) -> None:
        self.assertEqual(_bit_span(_Param("p", 2, 16)), (16, 32))  # type: ignore[arg-type]

    def test_the_bit_position_shifts_the_span(self) -> None:
        self.assertEqual(
            _bit_span(_Param("p", 1, 4, bit_position=2)),  # type: ignore[arg-type]
            (10, 14))

    def test_no_byte_position_cannot_be_placed(self) -> None:
        self.assertIsNone(_bit_span(_Param("p", None, 8)))  # type: ignore[arg-type]

    def test_no_static_length_cannot_be_placed(self) -> None:
        self.assertIsNone(_bit_span(_Param("p", 0, None)))  # type: ignore[arg-type]

    def test_zero_bits_occupy_nothing(self) -> None:
        """A zero-length span would satisfy the interval test against any span
        that contains its position, reporting an overlap over no bits at all."""
        self.assertIsNone(_bit_span(_Param("p", 3, 0)))  # type: ignore[arg-type]


class TestOverlapCondition(unittest.TestCase):

    def test_exhaustively_against_set_intersection(self) -> None:
        """Every pair of non-empty spans within 0..8, compared to ground truth."""
        for a_start, a_end, b_start, b_end in itertools.product(range(9), repeat=4):
            if a_end <= a_start or b_end <= b_start:
                continue
            placed = [((a_start, a_end), _Param("a", 0, 1)), ((b_start, b_end), _Param("b", 0, 1))]
            expected = bool(set(range(a_start, a_end)) & set(range(b_start, b_end)))
            self.assertEqual(
                bool(list(_overlaps(placed))),  # type: ignore[arg-type]
                expected,
                f"a=({a_start},{a_end}) b=({b_start},{b_end})")

    def test_declaration_order_does_not_matter(self) -> None:
        late = _Param("late", 4, 32)
        early = _Param("early", 5, 32)
        for order in ([late, early], [early, late]):
            placed, _ = _place(_Codec(order))  # type: ignore[arg-type]
            self.assertEqual(len(list(_overlaps(placed))), 1)


class TestPlace(unittest.TestCase):

    def test_unplaceable_parameters_are_counted_not_dropped_silently(self) -> None:
        placed, skipped = _place(
            _Codec([_Param("a", 0, 8), _Param("b", None, 8),
                    _Param("z", 1, 0)]))  # type: ignore[arg-type]
        self.assertEqual(len(placed), 1)
        self.assertEqual(skipped, 2)

    def test_a_none_parameter_is_skipped(self) -> None:
        """Non-strict mode can leave None entries in a parameter list."""
        placed, skipped = _place(_Codec([None, _Param("a", 0, 8)]))  # type: ignore[arg-type]
        self.assertEqual((len(placed), skipped), (1, 1))


class TestOverlappingParametersRule(unittest.TestCase):

    def test_findings_are_informational_never_errors(self) -> None:
        rule = OverlappingParameters()
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        for finding in rule.check(odxdb):
            self.assertIn(finding.severity, (Severity.DEBUG, Severity.INFO))

    def test_the_spec_field_admits_it_is_not_a_rule_of_the_standard(self) -> None:
        self.assertIn("standard permits", OverlappingParameters().spec)


class TestCodecEnumeration(unittest.TestCase):
    """Coverage guards: the enumeration must see the real objects.

    Attributes like ``service.request`` hand out weakref proxies, and a proxy
    fails ``isinstance`` against a runtime-checkable protocol. Walking those
    attributes silently inspected 3 of the 25 codec objects of the reference
    database; these tests pin the full number so that a regression cannot
    pass quietly again.
    """

    def test_every_codec_of_the_reference_database_is_seen(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        codecs = list(iter_codecs(odxdb))

        self.assertEqual(len(codecs), 25)

    def test_each_codec_is_seen_exactly_once(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        ids = [id(codec) for _, codec in iter_codecs(odxdb)]

        self.assertEqual(len(ids), len(set(ids)))

    def test_iter_objects_takes_the_type_to_look_for(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        services = [obj for _, obj in iter_objects(odxdb, DiagService)]

        self.assertTrue(services)
        self.assertTrue(all(isinstance(s, DiagService) for s in services))
        self.assertEqual(len(services), len({id(s) for s in services}))

    def test_the_document_name_is_part_of_the_location(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        for doc_name, _ in iter_codecs(odxdb):
            self.assertTrue(doc_name)


class TestNrcConstWithoutValue(unittest.TestCase):

    def test_an_overlapped_nrc_const_is_quiet(self) -> None:
        codec = _Codec(
            [_fake(NrcConstParameter, 2, 8, "reason"),
             _fake(ValueParameter, 2, 8, "reason_value")])

        findings = self._check(codec)

        self.assertEqual(findings, [])

    def test_an_unoverlapped_nrc_const_is_a_warning(self) -> None:
        codec = _Codec(
            [_fake(NrcConstParameter, 2, 8, "reason"),
             _fake(ValueParameter, 3, 8, "elsewhere")])

        findings = self._check(codec)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, Severity.WARNING)
        self.assertIn("reason", findings[0].message)

    def test_an_unplaceable_nrc_const_is_reported_at_debug(self) -> None:
        codec = _Codec([_fake(NrcConstParameter, None, None, "reason")])

        findings = self._check(codec)

        self.assertEqual([f.severity for f in findings], [Severity.DEBUG])

    def _check(self, codec: _Codec) -> list[Finding]:
        # check() is a generator: it has to be drained while the patch is in
        # effect, or the real enumeration runs when the caller iterates.
        rule = NrcConstWithoutValue()
        with mock.patch(
                "odxtools.checks.nrc_const_without_value.iter_codecs",
                return_value=[("doc", codec)]):
            return list(rule.check(object()))  # type: ignore[arg-type]


class TestReferenceDatabase(unittest.TestCase):

    def test_somersault_has_no_errors(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        errors = [str(f) for f in run_checks(odxdb) if f.severity == Severity.ERROR]

        self.assertEqual(errors, [])

    def test_the_reference_databases_have_no_warnings(self) -> None:
        for pdx in ("./examples/somersault.pdx", "./examples/somersault_modified.pdx"):
            odxdb = odxtools.load_pdx_file(pdx)

            warnings = [str(f) for f in run_checks(odxdb) if f.severity >= Severity.WARNING]

            self.assertEqual(warnings, [], pdx)

    def test_the_legitimate_overlap_of_flips_not_done_is_reported_as_info(self) -> None:
        """The NRC-CONST 'reason' shares its byte with the VALUE parameter
        'reason_value' on purpose; the overlap rule reports that at INFO and
        nothing louder. Pinned as the living example of both rules."""
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        infos = [f for f in run_checks(odxdb) if f.severity == Severity.INFO]

        self.assertEqual(len(infos), 1)
        self.assertIn("'reason'", infos[0].message)
        self.assertIn("'reason_value'", infos[0].message)
        self.assertEqual(infos[0].rule, "overlapping-parameters")


class TestNrcConstEncodeSemantics(unittest.TestCase):
    """The empirical basis of the nrc-const rule, pinned as a test.

    If odxtools ever makes NRC-CONST bytes directly encodable, this fails and
    the rule's justification has to be revisited.
    """

    def test_the_reason_is_chosen_through_the_overlapping_value(self) -> None:
        from odxtools.exceptions import EncodeError

        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")
        layer = odxdb.diag_layers.somersault_lazy
        service = layer.services.do_forward_flips
        response = next(r for r in service.negative_responses if r.short_name == "flips_not_done")
        request = bytes(service.encode_request(forward_soberness_check=0x12, num_flips=3))

        # the NRC-CONST itself still refuses a directly set value ...
        with self.assertRaises(EncodeError):
            response.encode(coded_request=request, reason=2, flips_successfully_done=1)

        # ... which is exactly why the overlapping VALUE parameter exists
        encoded = bytes(
            response.encode(coded_request=request, reason_value=2, flips_successfully_done=1))
        self.assertEqual(encoded[2], 2)

        decoded = layer.decode(encoded)[0]
        self.assertEqual(decoded.param_dict["reason"], 2)
        self.assertEqual(decoded.param_dict["reason_value"], 2)


class TestRunChecks(unittest.TestCase):

    def test_disabling_a_rule_skips_only_that_rule(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        findings = list(run_checks(odxdb, disabled=["nrc-const-without-value"]))

        self.assertFalse(any(f.rule == "nrc-const-without-value" for f in findings))
        self.assertTrue(any(f.rule == "overlapping-parameters" for f in findings))

    def test_disabling_an_unknown_rule_names_the_known_ones(self) -> None:
        odxdb = odxtools.load_pdx_file("./examples/somersault.pdx")

        with self.assertRaisesRegex(ValueError, "no-such-rule.*overlapping-parameters"):
            list(run_checks(odxdb, disabled=["no-such-rule"]))


class TestExitStatus(unittest.TestCase):
    """The exit status is what makes the tool usable in a pipeline."""

    def _run(self,
             findings: list[Finding],
             warnings_as_errors: bool = False,
             severity: str = "info",
             disable: list[str] | None = None) -> int:
        args = argparse.Namespace(
            pdx_file="unused",
            warnings_as_errors=warnings_as_errors,
            severity=severity,
            disable_rule=disable or [],
        )
        with mock.patch.object(_parser_utils, "load_file", return_value=object()), \
             mock.patch.object(check_tool, "run_checks", return_value=iter(findings)):
            try:
                check_tool.run(args)
            except SystemExit as error:
                return int(error.code or 0)
        return 0

    def _finding(self, severity: Severity) -> Finding:
        return Finding(rule="r", severity=severity, location=("Ecu",), message="m")

    def test_no_findings_is_a_success(self) -> None:
        self.assertEqual(self._run([]), 0)

    def test_info_findings_do_not_fail_a_pipeline(self) -> None:
        self.assertEqual(
            self._run([self._finding(Severity.INFO),
                       self._finding(Severity.DEBUG)]), 0)

    def test_a_warning_alone_does_not_fail(self) -> None:
        self.assertEqual(self._run([self._finding(Severity.WARNING)]), 0)

    def test_a_warning_fails_when_asked_for(self) -> None:
        self.assertEqual(self._run([self._finding(Severity.WARNING)], warnings_as_errors=True), 1)

    def test_an_error_fails(self) -> None:
        self.assertEqual(self._run([self._finding(Severity.ERROR)]), 1)

    def test_an_unknown_disabled_rule_exits_with_a_usage_error(self) -> None:
        args = argparse.Namespace(
            pdx_file="unused", warnings_as_errors=False, severity="info", disable_rule=["nope"])
        with mock.patch.object(_parser_utils, "load_file", return_value=object()), \
             mock.patch.object(check_tool, "run_checks",
                               side_effect=ValueError("cannot disable unknown rule(s) nope")):
            with self.assertRaises(SystemExit) as caught:
                check_tool.run(args)
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
