# SPDX-License-Identifier: MIT
"""Report the findings of the consistency checks for a database."""
import argparse
from collections.abc import Sequence
from typing import Any

from ..checks import DEFAULT_RULES, Severity, run_checks
from . import _parser_utils
from ._parser_utils import SubparsersList

_odxtools_tool_name_ = "check"


def _available_rules() -> str:
    """One line per rule: its name, padded to a column, and its description."""
    width = max(len(rule.name) for rule in DEFAULT_RULES)
    return "\n".join(f"{rule.name:<{width}}  {rule.description}" for rule in DEFAULT_RULES)


class _ListAvailableRules(argparse.Action):
    """Print the available rules and exit, the way ``--help`` does."""

    def __call__(self,
                 parser: argparse.ArgumentParser,
                 namespace: argparse.Namespace,
                 values: str | Sequence[Any] | None,
                 option_string: str | None = None) -> None:
        print(_available_rules())
        parser.exit()


class _DisableRules(argparse.Action):
    """Collect rule names, rejecting the ones no rule has."""

    def __call__(self,
                 parser: argparse.ArgumentParser,
                 namespace: argparse.Namespace,
                 values: str | Sequence[Any] | None,
                 option_string: str | None = None) -> None:
        names = [values] if isinstance(values, str) else list(values or [])
        known = {rule.name for rule in DEFAULT_RULES}
        if unknown := [name for name in names if name not in known]:
            parser.error(f"{option_string}: unknown rule(s) {', '.join(unknown)}; "
                         f"see --list-available-rules")
        setattr(namespace, self.dest, [*getattr(namespace, self.dest, []), *names])


def add_subparser(subparsers: SubparsersList) -> None:
    parser = subparsers.add_parser(
        _odxtools_tool_name_,
        description="Check a database for consistency findings",
        help="Check a database for consistency findings",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument(
        "--list-available-rules",
        action=_ListAvailableRules,
        nargs=0,
        default=argparse.SUPPRESS,
        help="Print the name and a one-line description of every rule, then exit",
    )

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
        "--disable-rules",
        action=_DisableRules,
        nargs="+",
        default=[],
        metavar="NAME",
        required=False,
        help="Skip the rules with these names (see --list-available-rules)",
    )


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)

    threshold = Severity[args.severity.upper()]
    rules = [rule for rule in DEFAULT_RULES if rule.name not in args.disable_rules]

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
