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
class MultiplexerDefaultCase(NamedElement):
    """This class represents a Default Case, which is selected when there are no cases defined in the Multiplexer."""
    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]

    def __post_init__(self) -> None:
        self._structure: Optional[BasicStructure] = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MultiplexerDefaultCase":
        """Reads a Default Case for a Multiplexer."""
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        structure_snref = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = odxrequire(structure_snref_elem.get("SHORT-NAME"))

        return MultiplexerDefaultCase(
            structure_ref=structure_ref, structure_snref=structure_snref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        if self.structure_snref:
            ddds = diag_layer.diag_data_dictionary_spec
            self._structure = odxrequire(ddds.structures.get(self.structure_snref))
