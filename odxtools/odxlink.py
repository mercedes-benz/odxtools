# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import typing

from dataclasses import dataclass, field
from xml.etree.ElementTree import Element
from typing import Optional, Any

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
        return self.doc_name.__hash__()

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
    doc_fragment : Optional[OdxDocFragment]

    def __hash__(self) -> int:
        return self.local_id.__hash__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OdxLinkId):
            return False

        if self.doc_fragment is None or other.doc_fragment is None:
            return self.local_id == other.local_id

        return \
            self.local_id == other.local_id and \
            self.doc_fragment == other.doc_fragment

    @staticmethod
    def from_et(et: Element, doc_fragment: OdxDocFragment) -> Optional["OdxLinkId"]:
        """Construct an OdxLinkId for a given XML node (ElementTree object).

        Returns None if the given XML node does not exhibit an ID.
        """

        local_id = et.attrib.get("ID")
        if local_id is None:
            return None

        return OdxLinkId(local_id, doc_fragment)

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

    #: The name of the document to which the `ref_id` refers to.
    ref_doc : Optional[OdxDocFragment] = None

    @staticmethod
    def from_et(et: Optional[Element], source_doc: OdxDocFragment) -> Optional["OdxLinkRef"]:
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
            doc_frag = OdxDocFragment(doc_ref, doc_type)
        else:
            doc_frag = source_doc

        return OdxLinkRef(id_ref, doc_frag)

    @staticmethod
    def from_id(odxid: OdxLinkId) -> "OdxLinkRef":
        """Construct an OdxLinkRef for a given OdxLinkId.
        """
        return OdxLinkRef(odxid.local_id, odxid.doc_fragment)

    def __contains__(self, id: OdxLinkId) -> bool:
        """
        Returns true iff a given OdxLinkId object is referenced.
        """

        if self.ref_doc is None or id.doc_fragment is None:
            return id.local_id == self.ref_id

        return \
            id.local_id == self.ref_id and \
            id.doc_fragment == self.ref_doc

class OdxLinkDatabase:
    """
    A database holding all objects which ehibit OdxLinkIds

    This can resolve references to such.
    """

    def __init__(self):
        self._db = {}

    def resolve(self, ref: OdxLinkRef) -> Any:
        """
        Resolve a reference to an object

        If the database does not contain any object which is referred to, a
        KeyError exception is raised.
        """
        assert isinstance(ref, OdxLinkRef)

        id = OdxLinkId(local_id=ref.ref_id,
                       doc_fragment=ref.ref_doc)

        return self._db[id]

    def resolve_lenient(self, ref: OdxLinkRef) -> Optional[Any]:
        """
        Resolve a reference to an object

        If the database does not contain any object which is referred to, None
        is returned.
        """
        assert isinstance(ref, OdxLinkRef)

        id = OdxLinkId(local_id=ref.ref_id,
                       doc_fragment=ref.ref_doc)

        return self._db.get(id)

    def update(self, new_entries : Dict[OdxLinkId, Any]) -> None:
        """
        Add a bunch of new objects to the ODXLINK database.

        The argument needs to be an OdxLinkId -> object dictionary.
        """
        self._db.update(new_entries)
