# SPDX-License-Identifier: MIT
"""Report the findings of the consistency checks for a database."""
import argparse

from ..checks import DEFAULT_RULES, Severity, run_checks
from . import _parser_utils
from ._parser_utils import SubparsersList

_odxtools_tool_name_ = "check"


def add_subparser(subparsers: SubparsersList) -> None:
    parser = subparsers.add_parser(
        _odxtools_tool_name_,
        description="Check a database for consistency findings",
        help="Check a database for consistency findings",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        required=False,
        help="Also exit with a non-zero status when only warnings were found",
    )

    parser.add_argument(
        "--severity",
        choices=[severity.name.lower() for severity in Severity],
        default=Severity.INFO.name.lower(),
        required=False,
        help="Lowest severity to report. Below info are the findings which say what "
        "was not inspected rather than what was found (default: %(default)s)",
    )

    parser.add_argument(
        "--disable-rule",
        action="append",
        default=[],
        metavar="NAME",
        choices=[rule.name for rule in DEFAULT_RULES],
        required=False,
        help="Skip the rule with this name; may be given several times. "
        "Known rules: " + ", ".join(sorted(rule.name for rule in DEFAULT_RULES)),
    )


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)

    threshold = Severity[args.severity.upper()]
    rules = [rule for rule in DEFAULT_RULES if rule.name not in args.disable_rule]

    counts = dict.fromkeys(Severity, 0)
    for finding in run_checks(odxdb, rules):
        counts[finding.severity] += 1
        if finding.severity >= threshold:
            print(finding)

    errors = counts[Severity.ERROR]
    warnings = counts[Severity.WARNING]

    print()
    print(f"{errors} error(s), {warnings} warning(s)")

    if errors or (warnings and args.warnings_as_errors):
        raise SystemExit(1)
