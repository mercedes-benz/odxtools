# SPDX-License-Identifier: MIT
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List
from xml.etree import ElementTree

from .element import IdentifiableElement
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class FunctionalClass(IdentifiableElement):
    """
    Corresponds to FUNCT-CLASS.
    """

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "FunctionalClass":

        kwargs = asdict(IdentifiableElement._from_et(et_element, doc_frags))

        return FunctionalClass(**kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
