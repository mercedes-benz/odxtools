# SPDX-License-Identifier: MIT
"""What a rule reports, and how much it matters."""
from dataclasses import dataclass, field
from enum import IntEnum


class Severity(IntEnum):
    """How much a finding matters.

    The values are numeric so that levels can be compared and filtered on,
    e.g. ``finding.severity >= Severity.INFO``. The numbers follow the
    convention of the :mod:`logging` module.

    ``ERROR`` is for something a conforming database cannot contain and which
    will make some operation on it fail or produce a wrong result. ``WARNING``
    is for something which is suspect but which the specification permits.
    ``INFO`` and ``DEBUG`` are for things worth seeing but not worth acting
    on, such as a permitted-but-unusual construct or an object a rule decided
    not to inspect.
    """

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


@dataclass(frozen=True, kw_only=True)
class Finding:
    """A single thing a rule reports."""

    #: name of the rule which produced this finding
    rule: str

    severity: Severity

    #: where in the database the finding is, as a path of short names
    #: starting with the name of the document which defines the object,
    #: e.g. ``("somersault", "flips_not_done")``
    location: tuple[str, ...] = field(default_factory=tuple)

    #: what was found, in one sentence, naming the objects involved
    message: str

    def __str__(self) -> str:
        where = "/".join(self.location)
        prefix = f"{where}: " if where else ""
        return f"{prefix}{self.severity.name.lower()}: {self.message} [{self.rule}]"
