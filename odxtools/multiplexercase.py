# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .compumethods.limit import Limit
from .element import NamedElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .odxtypes import AtomicOdxType, DataType
from .snrefcontext import SnRefContext
from .structure import Structure
from .utils import dataclass_fields_asdict


@dataclass
class MultiplexerCase(NamedElement):
    """This class represents a case which represents a range of keys of a multiplexer."""

    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]
    lower_limit: Limit
    upper_limit: Limit

    def __post_init__(self) -> None:
        self._structure: Optional[Structure]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MultiplexerCase":
        """Reads a case for a Multiplexer."""
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))
        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        structure_snref = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = odxrequire(structure_snref_elem.get("SHORT-NAME"))

        lower_limit = Limit.limit_from_et(
            odxrequire(et_element.find("LOWER-LIMIT")),
            doc_frags,
            value_type=None,
        )
        upper_limit = Limit.limit_from_et(
            odxrequire(et_element.find("UPPER-LIMIT")),
            doc_frags,
            value_type=None,
        )

        return MultiplexerCase(
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        raise RuntimeError("Calling MultiplexerCase._resolve_odxlinks() is not allowed. "
                           "Use ._mux_case_resolve_odxlinks().")

    def _mux_case_resolve_odxlinks(self, odxlinks: OdxLinkDatabase, *,
                                   key_physical_type: DataType) -> None:
        self._structure = None
        if self.structure_ref:
            self._structure = odxlinks.resolve(self.structure_ref, Structure)

        self.lower_limit.set_value_type(key_physical_type)
        self.upper_limit.set_value_type(key_physical_type)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.structure_snref:
            ddds = odxrequire(context.diag_layer).diag_data_dictionary_spec
            self._structure = resolve_snref(self.structure_snref, ddds.structures, Structure)

    def applies(self, value: AtomicOdxType) -> bool:
        return self.lower_limit.complies_to_lower(value) \
            and self.upper_limit.complies_to_upper(value)

    @property
    def structure(self) -> Optional[Structure]:
        return self._structure
