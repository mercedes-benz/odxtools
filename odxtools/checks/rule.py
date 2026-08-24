# SPDX-License-Identifier: MIT
"""The interface a consistency rule implements."""
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ..database import Database
from .finding import Finding


@runtime_checkable
class Rule(Protocol):
    """A single consistency rule."""

    #: identifier used to name the rule in output and to select or disable it
    name: str

    #: which part of the specification the rule draws on, so that the rule can
    #: be checked against the document rather than against its author's
    #: assumptions. Rules which do not enforce a requirement of the standard
    #: say so here explicitly.
    spec: str

    def check(self, database: Database) -> Iterable[Finding]:
        """Yield a finding for every object this rule reports."""
        ...
