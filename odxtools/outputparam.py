# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from deprecation import deprecated

from .dopbase import DopBase
from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class OutputParam(IdentifiableElement):
    dop_base_ref: OdxLinkRef
    oid: Optional[str]
    semantic: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "OutputParam":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        dop_base_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags))
        semantic = et_element.get("SEMANTIC")
        oid = et_element.get("OID")

        return OutputParam(dop_base_ref=dop_base_ref, semantic=semantic, oid=oid, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop_base = odxlinks.resolve(self.dop_base_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop_base(self) -> DopBase:
        """The data object property describing this parameter."""
        return self._dop_base

    @property
    @deprecated(details="use .dop_base")
    def dop(self) -> DopBase:
        return self._dop_base
