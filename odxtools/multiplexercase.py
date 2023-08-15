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
class MultiplexerCase:
    """This class represents a Case which represents multiple options in a Multiplexer."""

    short_name: str
    long_name: Optional[str]
    structure_ref: OdxLinkRef
    lower_limit: str
    upper_limit: str

    def __post_init__(self) -> None:
        self._structure: Optional[BasicStructure] = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MultiplexerCase":
        """Reads a Case for a Multiplexer."""
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")
        structure_ref = odxrequire(OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags))
        lower_limit = odxrequire(et_element.findtext("LOWER-LIMIT"))
        upper_limit = odxrequire(et_element.findtext("UPPER-LIMIT"))

        return MultiplexerCase(
            short_name=short_name,
            long_name=long_name,
            structure_ref=structure_ref,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._structure = odxlinks.resolve(self.structure_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
