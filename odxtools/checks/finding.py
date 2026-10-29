# SPDX-License-Identifier: MIT
"""What a rule reports, and how much it matters."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from ..odxlink import OdxLinkId


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

    #: how much this finding matters. A rule may emit findings of different
    #: severities, e.g. a note about what it could not inspect next to what
    #: it found.
    severity: Severity

    #: the object the finding is about
    object: Any

    #: what was found, in one sentence, naming the objects involved
    message: str

    @property
    def odx_id(self) -> OdxLinkId | None:
        """The ODX ID of the object, or ``None`` if it has none."""
        odx_id = getattr(self.object, "odx_id", None)
        return odx_id if isinstance(odx_id, OdxLinkId) else None

    @property
    def short_name(self) -> str | None:
        """The short name of the object, or ``None`` if it has none."""
        short_name = getattr(self.object, "short_name", None)
        return short_name if isinstance(short_name, str) else None

    @property
    def short_name_path(self) -> str | None:
        """Where to find the object: the short names of the documents it is
        registered under, followed by its own, joined by dots.

        The documents are taken from the document fragments of the object's
        ODX ID, i.e. the DIAG-LAYER-CONTAINER and the DIAG-LAYER (or the
        COMPARAM-SUBSET, ...) which define it. Objects do not know their
        parents, so what lies in between, e.g. the service a response belongs
        to, is not part of the path.
        """
        short_name = self.short_name
        if short_name is None:
            return None
        odx_id = self.odx_id
        doc_names = [] if odx_id is None else [frag.doc_name for frag in odx_id.doc_fragments]
        return ".".join([*doc_names, short_name])

    def __str__(self) -> str:
        where = self.short_name_path or type(self.object).__name__
        if (odx_id := self.odx_id) is not None:
            where = f"{where} ({odx_id.local_id})"
        return f"{where}: {self.severity.name.lower()}: {self.message} [{self.rule}]"
