# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext
from .structure import Structure
from .utils import dataclass_fields_asdict


@dataclass
class MultiplexerDefaultCase(NamedElement):
    """This class represents a Default Case, which is selected when there are no cases defined in the Multiplexer."""
    structure_ref: OdxLinkRef | None
    structure_snref: str | None

    @property
    def structure(self) -> Structure | None:
        return self._structure

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: list[OdxDocFragment]) -> "MultiplexerDefaultCase":
        """Reads a default case for a multiplexer."""
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        structure_snref = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = odxrequire(structure_snref_elem.get("SHORT-NAME"))

        return MultiplexerDefaultCase(
            structure_ref=structure_ref, structure_snref=structure_snref, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._structure = None
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref, Structure)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.structure_snref:
            ddds = odxrequire(context.diag_layer).diag_data_dictionary_spec
            self._structure = resolve_snref(self.structure_snref, ddds.structures, Structure)
