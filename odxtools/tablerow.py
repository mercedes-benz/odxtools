# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

from .dataobjectproperty import DopBase
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import AtomicOdxType
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .structures import BasicStructure
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer
    from .table import Table


@dataclass
class TableRow:
    """This class represents a TABLE-ROW."""

    odx_id: OdxLinkId
    short_name: str
    long_name: str
    key: int
    structure_ref: Optional[OdxLinkRef]
    dop_ref: Optional[OdxLinkRef]
    description: Optional[str]
    semantic: Optional[str]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self) -> None:
        self._structure: Optional[DopBase] = None
        self._dop: Optional[DopBase] = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "TableRow":
        """Reads a TABLE-ROW."""
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        semantic = et_element.get("SEMANTIC")
        description = create_description_from_et(et_element.find("DESC"))
        key = et_element.findtext("KEY")
        structure_ref = None
        if et_element.find("STRUCTURE-REF") is not None:
            structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        dop_ref = None
        if et_element.find("DATA-OBJECT-PROP-REF") is not None:
            dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags)
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return TableRow(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            semantic=semantic,
            description=description,
            key=key,
            structure_ref=structure_ref,
            dop_ref=dop_ref,
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)
        if self.dop_ref is not None:
            self._dop = odxlinks.resolve(self.dop_ref)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

    @property
    def structure(self) -> Optional[DopBase]:
        """The structure associated with this table row."""
        return self._structure

    @property
    def dop(self) -> Optional[DopBase]:
        """The dop object resolved by dop_ref."""
        return self._dop

    def __repr__(self) -> str:
        return (f"TableRow('{self.short_name}', " + ", ".join([
            f"key='{self.key}'",
            f"structure_ref='{self.structure_ref}'",
            f"dop_ref='{self.dop_ref}'",
        ]) + ")")
