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


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)

    errors = warnings = 0
    for finding in run_checks(odxdb):
        print(finding)
        if finding.severity is Severity.ERROR:
            errors += 1
        else:
            warnings += 1

    if errors or warnings:
        print(f"\n{errors} error(s), {warnings} warning(s)")
    else:
        print("no findings")

    if errors or (warnings and args.warnings_as_errors):
        raise SystemExit(1)
