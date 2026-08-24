# SPDX-License-Identifier: MIT
"""The interface a consistency rule implements."""
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ..database import Database
from .finding import Finding


@runtime_checkable
class Rule(Protocol):
    """A single consistency rule."""

    #: identifier used to name the rule in output and to select it
    name: str

    def check(self, database: Database) -> Iterable[Finding]:
        """Yield a finding for every object this rule objects to."""
        ...
