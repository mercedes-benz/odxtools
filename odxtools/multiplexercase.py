# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .element import NamedElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class MultiplexerCase(NamedElement):
    """This class represents a Case which represents multiple options in a Multiplexer."""

    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]
    lower_limit: str
    upper_limit: str

    def __post_init__(self) -> None:
        self._structure: BasicStructure

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MultiplexerCase":
        """Reads a Case for a Multiplexer."""
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))
        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        structure_snref = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = odxrequire(structure_snref_elem.get("SHORT-NAME"))

        lower_limit = odxrequire(et_element.findtext("LOWER-LIMIT"))
        upper_limit = odxrequire(et_element.findtext("UPPER-LIMIT"))

        return MultiplexerCase(
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref:
            self._structure = odxlinks.resolve(self.structure_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.structure_snref:
            ddds = diag_layer.diag_data_dictionary_spec
            self._structure = odxrequire(ddds.structures.get(self.structure_snref))

    @property
    def structure(self) -> BasicStructure:
        return self._structure
