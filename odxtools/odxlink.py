# SPDX-License-Identifier: MIT
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, TypeVar, overload
from xml.etree import ElementTree

from .exceptions import OdxWarning, odxassert, odxraise, odxrequire
from .nameditemlist import OdxNamed, TNamed
from .odxdoccontext import OdxDocContext


class DocType(Enum):
    FLASH = "FLASH"
    CONTAINER = "CONTAINER"
    LAYER = "LAYER"
    MULTIPLE_ECU_JOB_SPEC = "MULTIPLE-ECU-JOB-SPEC"
    COMPARAM_SPEC = "COMPARAM-SPEC"
    VEHICLE_INFO_SPEC = "VEHICLE-INFO-SPEC"
    COMPARAM_SUBSET = "COMPARAM-SUBSET"
    ECU_CONFIG = "ECU-CONFIG"
    FUNCTION_DICTIONARY_SPEC = "FUNCTION-DICTIONARY-SPEC"


@dataclass(frozen=True)
class OdxDocFragment:
    doc_name: str
    doc_type: DocType


@dataclass(frozen=True)
class OdxLinkId:
    """The identifier of an ODX object.

    A full ODX ID comprises the document fragment where the object
    is located (i.e., the short name object beneath the root object of the
    currently read XMl file) plus a locally unique identifier for the object.

    OdxLinkIds are hashable.
    """

    #: An identifier that is (hopefully) locally unique within the
    #: relevant document fragment
    local_id: str

    #: The name and type of the document fragment to which the
    #: `local_id` is relative to
    doc_fragments: tuple[OdxDocFragment] | tuple[OdxDocFragment, OdxDocFragment]

    def __hash__(self) -> int:
        # we do not hash about the document fragment here, because
        # document fragments are handled using separate sub-databases,
        # i.e. the same OdxId object can be put into all of them.
        return hash(self.local_id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OdxLinkId):
            return False

        # if the local ID is different, the whole id is different
        if self.local_id != other.local_id:
            return False

        # the document fragments must be identical for the IDs to be identical
        return self.doc_fragments == other.doc_fragments

    def __str__(self) -> str:
        return f"OdxLinkId('{self.local_id}')"

    @staticmethod
    def from_et(et: ElementTree.Element, context: OdxDocContext) -> Optional["OdxLinkId"]:
        """Construct an OdxLinkId for a given XML node (ElementTree object).

        Returns None if the given XML node does not exhibit an ID.
        """

        local_id = et.attrib.get("ID")
        if local_id is None:
            return None

        return OdxLinkId(local_id, context.doc_fragments)


@dataclass
class OdxLinkRef:
    """A reference to an ODX object.

    OdxLinkRefs are similar to OdxLinkIds, with the difference that the document
    of the referred-to object does not need to be specified. (In this case, it
    means "use the document where the referring object is located in")
    """

    #: The local identifier of the object which is referred to
    ref_id: str

    #: The document fragments to which the `ref_id` refers to (in reverse order)
    ref_docs: tuple[OdxDocFragment, ...]

    # TODO: this is difficult because OdxLinkRef is derived from and
    # we do not want having to specify it mandatorily
    #revision: Optional[str] = None

    @overload
    @staticmethod
    def from_et(et: None, context: OdxDocContext) -> None:
        ...

    @overload
    @staticmethod
    def from_et(et: ElementTree.Element, context: OdxDocContext) -> "OdxLinkRef":
        ...

    @staticmethod
    def from_et(et: ElementTree.Element | None, context: OdxDocContext) -> Optional["OdxLinkRef"]:
        """Construct an OdxLinkRef for a given XML node (ElementTree object).

        Returns None if the given XML node does not represent a reference.
        """

        if et is None:
            return None

        id_ref = et.attrib.get("ID-REF")
        if id_ref is None:
            odxraise(f"Tag {et.tag} is not a ODXLINK reference")
            return None

        docref = et.attrib.get("DOCREF")
        doctype_attr = et.attrib.get("DOCTYPE")

        odxassert((docref is not None and doctype_attr is not None) or
                  (docref is None and doctype_attr is None),
                  "DOCREF and DOCTYPE must both either be specified or omitted")

        doctype = None
        if doctype_attr is not None:
            try:
                doctype = DocType(doctype_attr)
            except ValueError:
                odxraise(f"Encountered unknown document type '{doctype_attr}'")

        # if the target document fragment is specified by the
        # reference, use it, else use the document fragment containing
        # the reference.
        if docref is None:
            doc_frags = context.doc_fragments
        else:
            doc_frags = (OdxDocFragment(docref, odxrequire(doctype)),)

        return OdxLinkRef(id_ref, doc_frags)

    @staticmethod
    def from_id(odxid: OdxLinkId) -> "OdxLinkRef":
        """Construct an OdxLinkRef for a given OdxLinkId."""
        return OdxLinkRef(odxid.local_id, odxid.doc_fragments)

    def __str__(self) -> str:
        return f"OdxLinkRef('{self.ref_id}')"


T = TypeVar("T")


class OdxLinkDatabase:
    """
    A database holding all objects which exhibit OdxLinkIds

    This can resolve ODXLINK references.
    """

    def __init__(self) -> None:
        self._db: dict[OdxDocFragment, dict[str, Any]] = {}

    @overload
    def resolve(self, ref: OdxLinkRef, expected_type: None = None) -> Any:
        ...

    @overload
    def resolve(self, ref: OdxLinkRef, expected_type: type[T]) -> T:
        ...

    def resolve(self, ref: OdxLinkRef, expected_type: Any | None = None) -> Any:
        """
        Resolve a reference to an object

        If the database does not contain any object which is referred to, a
        KeyError exception is raised.
        """
        for ref_frag in reversed(ref.ref_docs):
            doc_frag_db = self._db.get(ref_frag)
            if doc_frag_db is None:
                # No object featured by the database uses the document
                # fragment mentioned by the reference. This should not
                # happen for correct ODX databases...
                warnings.warn(
                    f"Warning: Unknown document fragment {ref_frag} "
                    f"when resolving reference {ref}",
                    OdxWarning,
                    stacklevel=1,
                )
                continue

            # locate an object exhibiting with the referenced local ID
            # in the ID database for the document fragment
            if (obj := doc_frag_db.get(ref.ref_id)) is not None:
                if expected_type is not None and not isinstance(obj, expected_type):
                    odxraise(f"Referenced object for link {ref.ref_id} is of type "
                             f"{type(obj).__name__} which is not a subclass of expected "
                             f"type {expected_type.__name__}")

                return obj

        odxraise(
            f"ODXLINK reference {ref} could not be resolved for any "
            f"of the document fragments {ref.ref_docs}", KeyError)
        return None

    @overload
    def resolve_lenient(self, ref: OdxLinkRef, expected_type: None = None) -> Any:
        ...

    @overload
    def resolve_lenient(self, ref: OdxLinkRef, expected_type: type[T]) -> T | None:
        ...

    def resolve_lenient(self, ref: OdxLinkRef, expected_type: Any | None = None) -> Any | None:
        """
        Resolve a reference to an object

        If the database does not contain any object which is referred to, None
        is returned.
        """

        for ref_frag in reversed(ref.ref_docs):
            doc_frag_db = self._db.get(ref_frag)
            if doc_frag_db is None:
                # No object featured by the database uses the document
                # fragment mentioned by the reference. This should not
                # happen for correct databases...
                warnings.warn(
                    f"Warning: Unknown document fragment {ref_frag} "
                    f"when resolving reference {ref}",
                    OdxWarning,
                    stacklevel=1,
                )
                continue

            if (obj := doc_frag_db.get(ref.ref_id)) is not None:
                if expected_type is not None:
                    odxassert(isinstance(obj, expected_type))

                return obj

        return None

    def update(self, new_entries: dict[OdxLinkId, Any], *, overwrite: bool = True) -> None:
        """
        Add a bunch of new objects to the ODXLINK database.

        The argument needs to be an OdxLinkId -> object dictionary.
        """

        # put all new objects into the databases for the document
        # fragments which it specifies
        for odx_id, obj in new_entries.items():
            for doc_frag in odx_id.doc_fragments:
                if doc_frag not in self._db:
                    self._db[doc_frag] = {}

                if overwrite:
                    self._db[doc_frag][odx_id.local_id] = obj
                else:
                    self._db[doc_frag].setdefault(odx_id.local_id, obj)


@overload
def resolve_snref(target_short_name: str,
                  items: Iterable[OdxNamed],
                  expected_type: None = None,
                  *,
                  lenient: None = None) -> Any:
    """Resolve a short name reference given a sequence of candidate objects"""
    ...


@overload
def resolve_snref(target_short_name: str,
                  items: Iterable[OdxNamed],
                  expected_type: type[TNamed],
                  *,
                  lenient: None = None) -> TNamed:
    ...


@overload
def resolve_snref(target_short_name: str,
                  items: Iterable[OdxNamed],
                  expected_type: type[TNamed],
                  *,
                  lenient: bool = True) -> TNamed | None:
    ...


def resolve_snref(target_short_name: str,
                  items: Iterable[OdxNamed],
                  expected_type: Any = None,
                  lenient: bool | None = None) -> Any:
    candidates = [x for x in items if x.short_name == target_short_name]

    if not candidates:
        if not lenient:
            odxraise(f"Cannot resolve short name reference to '{target_short_name}'")
        return None
    elif len(candidates) > 1:
        odxraise(f"Cannot uniquely resolve short name reference to '{target_short_name}'")
    elif expected_type is not None and not isinstance(candidates[0], expected_type):
        odxraise(f"Reference '{target_short_name}' points to a {type(candidates[0]).__name__}"
                 f"object while expecting {expected_type.__name__}")

    return candidates[0]
