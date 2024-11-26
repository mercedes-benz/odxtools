# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .dopbase import DopBase
from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class OutputParam(IdentifiableElement):
    dop_base_ref: OdxLinkRef
    semantic: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "OutputParam":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        dop_base_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags))
        semantic = et_element.get("SEMANTIC")

        return OutputParam(dop_base_ref=dop_base_ref, semantic=semantic, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop_base = odxlinks.resolve(self.dop_base_ref, DopBase)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass

    @property
    def dop_base(self) -> DopBase:
        """The data object property describing this parameter."""
        return self._dop_base
