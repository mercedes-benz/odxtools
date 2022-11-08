# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import typing
import warnings

from dataclasses import dataclass, field
from xml.etree.ElementTree import Element
from typing import Optional, Any, List
from .exceptions import OdxWarning

@dataclass(frozen=True)
class OdxDocFragment:
    doc_name : str
    doc_type : Optional[str]

    def __eq__(self, other) -> bool:
        if other is None:
            # if the other document fragment is not specified, we treat it as a wildcard...
            return True

        # the ODX spec says that the doctype can be ignored...
        return self.doc_name == other.doc_name

    def __hash__(self) -> int:
        # only the document name is relevant for the hash value
        return hash(self.doc_name) + hash(self.doc_type)

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
    local_id : str

    #: The name and type of the document fragment to which the
    #: `local_id` is relative to
    doc_fragments : List[OdxDocFragment]

    def __hash__(self) -> int:
        # we do not hash about the document fragment here, because
        # document fragments are handled using separate sub-databases,
        # i.e. the same OdxId object can be put into all of them.
        return hash(self.local_id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OdxLinkId):
            return False

        # we do take the document fragment into consideration here, because
        # document fragments are handled using separate sub-databases,
        # i.e. the same OdxId object can be put into all of them.
        return self.local_id == other.local_id

    @staticmethod
    def from_et(et: Element, doc_fragments: List[OdxDocFragment]) -> Optional["OdxLinkId"]:
        """Construct an OdxLinkId for a given XML node (ElementTree object).

        Returns None if the given XML node does not exhibit an ID.
        """

        local_id = et.attrib.get("ID")
        if local_id is None:
            return None

        return OdxLinkId(local_id, doc_fragments)

from typing import Dict, Union, Optional, Any
from dataclasses import dataclass, field, replace
from xml.etree.ElementTree import Element

@dataclass(frozen=True)
class OdxLinkRef:
    """A reference to an ODX object.

    OdxLinkRefs are similar to OdxLinkIds, with the difference that the document
    of the referred-to object does not need to be specified. (In this case, it
    means "use the document where the referring object is located in")
    """

    #: The local identifier of the object which is referred to
    ref_id : str

    #: The document fragments to which the `ref_id` refers to (in reverse order)
    ref_docs : List[OdxDocFragment]

    @staticmethod
    def from_et(et: Optional[Element], source_doc_frags: List[OdxDocFragment]) -> Optional["OdxLinkRef"]:
        """Construct an OdxLinkRef for a given XML node (ElementTree object).

        Returns None if the given XML node does not represent a reference.
        """

        if et is None:
            return None

        id_ref = et.attrib.get("ID-REF")
        if id_ref is None:
            return None

        doc_ref = et.attrib.get("DOCREF")
        doc_type = et.attrib.get("DOCTYPE")

        assert \
            (doc_ref is not None and doc_type is not None) or \
            (doc_ref is None and doc_type is None), \
            "DOCREF and DOCTYPE must both either be specified or omitted"

        # if the target document fragment is specified by the
        # reference, use it, else use the document fragment containing
        # the reference.
        if doc_ref is not None:
            doc_frags = [OdxDocFragment(doc_ref, doc_type)]
        else:
            doc_frags = source_doc_frags

        return OdxLinkRef(id_ref, doc_frags)

    @staticmethod
    def from_id(odxid: OdxLinkId) -> "OdxLinkRef":
        """Construct an OdxLinkRef for a given OdxLinkId.
        """
        return OdxLinkRef(odxid.local_id, odxid.doc_fragments)

    def __contains__(self, odx_id: OdxLinkId) -> bool:
        """
        Returns true iff a given OdxLinkId object is referenced.
        """

        # we must reference at to at least of the ID's document
        # fragments
        if not any([ref_doc in odx_id.doc_fragments for ref_doc in self.ref_docs]):
            return False

        # the local ID of the reference and the object ID must match
        return odx_id.local_id == self.ref_id

class OdxLinkDatabase:
    """
    A database holding all objects which ehibit OdxLinkIds

    This can resolve references to such.
    """

    def __init__(self) -> None:
        self._db: Dict[OdxDocFragment, Dict[OdxLinkId, Any]] = {}

    def resolve(self, ref: OdxLinkRef) -> Any:
        """
        Resolve a reference to an object

        If the database does not contain any object which is referred to, a
        KeyError exception is raised.
        """
        assert isinstance(ref, OdxLinkRef)

        odx_id = OdxLinkId(ref.ref_id, ref.ref_docs)
        for ref_frag in reversed(ref.ref_docs):
            doc_frag_db = self._db.get(ref_frag)
            if doc_frag_db is None:
                # No object featured by the database uses the document
                # fragment mentioned by the reference. This should not
                # happen for correct databases...
                warnings.warn(f"Warning: Unknown document fragment {ref_frag} "
                              f"when resolving reference {ref}", OdxWarning)
                continue

            obj = doc_frag_db.get(odx_id)
            if obj is not None:
                return obj

        raise KeyError(f"ODXLINK reference {ref} could not be resolved for any "
                       f"of the document fragments {ref.ref_docs}")

    def resolve_lenient(self, ref: OdxLinkRef) -> Optional[Any]:
        """
        Resolve a reference to an object

        If the database does not contain any object which is referred to, None
        is returned.
        """
        assert isinstance(ref, OdxLinkRef)

        odx_id = OdxLinkId(ref.ref_id, ref.ref_docs)
        for ref_frag in reversed(ref.ref_docs):
            doc_frag_db = self._db.get(ref_frag)
            if doc_frag_db is None:
                # No object featured by the database uses the document
                # fragment mentioned by the reference. This should not
                # happen for correct databases...
                warnings.warn(f"Warning: Unknown document fragment {ref_frag} "
                              f"when resolving reference {ref}", OdxWarning)
                continue

            obj = doc_frag_db.get(odx_id)
            if obj is not None:
                return obj

        return None

    def update(self, new_entries : Dict[OdxLinkId, Any]) -> None:
        """
        Add a bunch of new objects to the ODXLINK database.

        The argument needs to be an OdxLinkId -> object dictionary.
        """

        # put all new objects into the databases for the document
        # fragments which it specifies
        for odx_id, obj in new_entries.items():
            for doc_frag in odx_id.doc_fragments:
                if doc_frag not in self._db:
                    self._db[doc_frag] = dict()

                self._db[doc_frag][odx_id] = obj
