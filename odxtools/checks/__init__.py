# SPDX-License-Identifier: MIT
"""Consistency checks for a loaded database.

A check reports things which are worth a reader's attention: parameters which
share bits, an NRC-CONST which nothing exposes, and so on. Loading a database
does not reject these; the checks make them visible.

Each rule lives in its own module and is registered in :data:`DEFAULT_RULES`
below. A rule receives the database and yields :class:`Finding` objects; it is
not expected to raise, and a rule which cannot decide about an object reports
that at :attr:`Severity.DEBUG` rather than guessing.
"""
from collections.abc import Iterable, Iterator

from ..database import Database
from .finding import Finding, Severity
from .nrc_const_without_value import NrcConstWithoutValue
from .overlapping_parameters import OverlappingParameters
from .rule import Rule

__all__ = [
    "DEFAULT_RULES",
    "Finding",
    "Rule",
    "Severity",
    "run_checks",
]

#: The rules which :func:`run_checks` applies by default.
DEFAULT_RULES: tuple[Rule, ...] = (
    OverlappingParameters(),
    NrcConstWithoutValue(),
)


def run_checks(database: Database, rules: Iterable[Rule] = DEFAULT_RULES) -> Iterator[Finding]:
    """Apply ``rules`` to ``database`` and yield what they report.

    Args:
        database: the database to inspect
        rules: the rules to apply, :data:`DEFAULT_RULES` unless given
    """
    for rule in rules:
        yield from rule.check(database)
