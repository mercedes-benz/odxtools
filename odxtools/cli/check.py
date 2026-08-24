# SPDX-License-Identifier: MIT
import argparse

from ..checks import Severity, run_checks
from . import _parser_utils
from ._parser_utils import SubparsersList

# name of the tool
_odxtools_tool_name_ = "check"


def add_subparser(subparsers: SubparsersList) -> None:
    parser = subparsers.add_parser(
        "check",
        description="Check a database for inconsistencies",
        help="Report parts of a database which a conforming one should not contain",
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
        choices=[severity.value for severity in Severity],
        default=Severity.WARNING.value,
        required=False,
        help="Lowest severity to report. Below warning are the findings which say what was "
        "not inspected rather than what is wrong (default: %(default)s)",
    )


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)

    # Ordered loudest first, so a threshold admits everything at least as loud.
    order = (Severity.ERROR, Severity.WARNING, Severity.INFO, Severity.DEBUG)
    threshold = order.index(Severity(args.severity))

    counts = dict.fromkeys(order, 0)
    for finding in run_checks(odxdb):
        counts[finding.severity] += 1
        if order.index(finding.severity) <= threshold:
            print(finding)

    errors = counts[Severity.ERROR]
    warnings = counts[Severity.WARNING]

    print()
    print(f"{errors} error(s), {warnings} warning(s)")

    if errors or (warnings and args.warnings_as_errors):
        raise SystemExit(1)
