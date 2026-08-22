# SPDX-License-Identifier: MIT
"""Consistency checks for a loaded database.

A check reports things which a conforming database should not contain, but
which loading it does not necessarily reject: parameters which occupy the
same bits, references which cannot be told apart, and so on.

Each rule lives in its own module and is registered in :data:`RULES` below.
A rule receives the database and yields :class:`Finding` objects; it is not
expected to raise, and a rule which cannot decide about an object should say
nothing rather than guess.
"""
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

from ..database import Database


class Severity(Enum):
    """How much a finding matters.

    ``ERROR`` is for something a conforming database cannot contain and which
    will make some operation on it fail or produce a wrong result. ``WARNING``
    is for something which is suspect but which the specification permits.
    """

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, kw_only=True)
class Finding:
    """A single thing a rule objects to."""

    #: name of the rule which produced this finding
    rule: str

    severity: Severity

    #: where in the database the finding is, as a path of short names,
    #: e.g. ``("MyEcu", "MyService", "MyResponse")``
    location: tuple[str, ...] = field(default_factory=tuple)

    #: what is wrong, in one sentence, naming the objects involved
    message: str

    def __str__(self) -> str:
        where = "/".join(self.location)
        prefix = f"{where}: " if where else ""
        return f"{self.severity.value}: {prefix}{self.message} [{self.rule}]"


@runtime_checkable
class Rule(Protocol):
    """A single consistency rule."""

    #: identifier used to name the rule in output and to select it
    name: str

    def check(self, database: Database) -> Iterable[Finding]:
        """Yield a finding for every object this rule objects to."""
        ...


from .overlapping_parameters import OverlappingParameters  # noqa: E402

#: The rules which :func:`run_checks` applies by default. New rules are added
#: here once they are known not to report conforming databases.
RULES: tuple[Rule, ...] = (OverlappingParameters(),)


def run_checks(database: Database, rules: Iterable[Rule] | None = None) -> Iterator[Finding]:
    """Apply ``rules`` to ``database`` and yield what they object to.

    Args:
        database: the database to inspect
        rules: the rules to apply, defaulting to :data:`RULES`
    """
    for rule in RULES if rules is None else rules:
        yield from rule.check(database)
