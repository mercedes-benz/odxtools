# SPDX-License-Identifier: MIT
"""Enumerate the objects of a database which the rules inspect."""
from collections.abc import Iterator
from typing import TypeVar

from ..compositecodec import CompositeCodec
from ..database import Database

T = TypeVar("T")


def iter_objects(database: Database, of_type: type[T]) -> Iterator[tuple[str, T]]:
    """``(doc_name, obj)`` for every object of ``of_type``, exactly once.

    The objects are taken from the link database rather than from attributes
    like ``service.request``: those attributes may hand out ``weakref`` proxies,
    and a proxy does not pass an ``isinstance`` check against a
    runtime-checkable protocol, which would silently drop the object.
    """
    seen: set[int] = set()
    for doc_fragment, obj in database.odxlinks.objects():
        if isinstance(obj, of_type) and id(obj) not in seen:
            seen.add(id(obj))
            yield doc_fragment.doc_name, obj


def iter_codecs(database: Database) -> Iterator[tuple[str, CompositeCodec]]:
    """The parameter-carrying objects of ``database``, exactly once each."""
    # mypy rejects a protocol class where type[T] is expected because it deems
    # type[T] instantiable (python/mypy#4717); of_type is only given to
    # isinstance, for which a runtime-checkable protocol is fine.
    return iter_objects(database, CompositeCodec)  # type: ignore[type-abstract]
