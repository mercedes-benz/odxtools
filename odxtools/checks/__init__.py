# SPDX-License-Identifier: MIT
"""Consistency checks for a loaded database.

A check reports things which a conforming database should not contain, but
which loading it does not necessarily reject: parameters which occupy the
same bits, references which cannot be told apart, and so on.

Each rule lives in its own module and is registered in :data:`DEFAULT_RULES`
below. A rule receives the database and yields :class:`Finding` objects; it is
not expected to raise, and a rule which cannot decide about an object should
say nothing rather than guess.
"""
from collections.abc import Iterable, Iterator

from ..database import Database
from .finding import Finding, Severity
from .overlapping_parameters import OverlappingParameters
from .rule import Rule

__all__ = [
    "DEFAULT_RULES",
    "Finding",
    "OverlappingParameters",
    "Rule",
    "Severity",
    "run_checks",
]

#: The rules which :func:`run_checks` applies by default. New rules are added
#: here once they are known not to report conforming databases.
DEFAULT_RULES: tuple[Rule, ...] = (OverlappingParameters(),)


def run_checks(database: Database, rules: Iterable[Rule] | None = None) -> Iterator[Finding]:
    """Apply ``rules`` to ``database`` and yield what they object to.

    Args:
        database: the database to inspect
        rules: the rules to apply, defaulting to :data:`DEFAULT_RULES`
    """
    selected_rules = DEFAULT_RULES if rules is None else rules
    for rule in selected_rules:
        yield from rule.check(database)
