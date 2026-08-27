# SPDX-License-Identifier: MIT
"""The interface a consistency rule implements, and what a rule inspects."""
from collections.abc import Iterable
from typing import Protocol, TypeGuard, runtime_checkable

from ..basicstructure import BasicStructure
from ..compositecodec import CompositeCodec
from ..database import Database
from ..request import Request
from ..response import Response
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


def is_composite_codec(obj: object) -> TypeGuard[CompositeCodec]:
    """Whether ``obj`` is one of the objects which carry a list of parameters.

    The test is against the concrete classes rather than against the
    :class:`~odxtools.compositecodec.CompositeCodec` protocol. Up to Python
    3.11, ``isinstance`` against a runtime-checkable protocol evaluates every
    property the protocol names, so an object whose ``required_parameters``
    cannot be computed, i.e. one with a broken parameter, fails the check and
    is skipped without a word, although it is exactly what a rule is there to
    look at.
    """
    return isinstance(obj, (BasicStructure, Request, Response))
