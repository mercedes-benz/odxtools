# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class MultiplexerDefaultCase:
    """This class represents a Default Case, which is selected when there are no cases defined in the Multiplexer."""

    short_name: str
    long_name: Optional[str]
    structure_ref: Optional[OdxLinkRef]

    def __post_init__(self) -> None:
        self._structure: Optional[BasicStructure] = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MultiplexerDefaultCase":
        """Reads a Default Case for a Multiplexer."""
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")

        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)

        return MultiplexerDefaultCase(
            short_name=short_name,
            long_name=long_name,
            structure_ref=structure_ref,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
