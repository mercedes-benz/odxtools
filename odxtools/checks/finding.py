# SPDX-License-Identifier: MIT
"""What a rule reports, and how much it matters."""
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """How much a finding matters.

    ``ERROR`` is for something a conforming database cannot contain and which
    will make some operation on it fail or produce a wrong result. ``WARNING``
    is for something which is suspect but which the specification permits.
    ``INFO`` and ``DEBUG`` are for things worth saying but not worth acting on,
    such as an object a rule decided not to inspect.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


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
        return f"{prefix}{self.severity.value}: {self.message} [{self.rule}]"
