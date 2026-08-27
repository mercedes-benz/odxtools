# SPDX-License-Identifier: MIT
"""Enumerate the objects of a database which the rules inspect."""
from collections.abc import Iterator
from typing import TypeVar

from ..compositecodec import CompositeCodec
from ..database import Database

T = TypeVar("T")


def iter_objects(database: Database, of_type: type[T]) -> Iterator[tuple[str, str, T]]:
    """``(doc_name, odx_id, obj)`` for every object of ``of_type``, exactly once.

    The objects are taken from the link database rather than from attributes
    like ``service.request``: those attributes may hand out ``weakref`` proxies,
    and a proxy does not pass an ``isinstance`` check against a
    runtime-checkable protocol, which would silently drop the object.
    """
    for obj in database.odxlinks.objects():
        if isinstance(obj, of_type):
            yield obj.odx_id.doc_fragments[0].doc_name, obj.odx_id.local_id, obj


def iter_codecs(database: Database) -> Iterator[tuple[str, str, CompositeCodec]]:
    """The parameter-carrying objects of ``database``, exactly once each."""
    # mypy rejects a protocol class where type[T] is expected because it deems
    # type[T] instantiable (python/mypy#4717); of_type is only given to
    # isinstance, for which a runtime-checkable protocol is fine.
    return iter_objects(database, CompositeCodec)  # type: ignore[type-abstract]
