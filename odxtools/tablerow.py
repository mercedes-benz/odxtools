# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

from .dataobjectproperty import DataObjectProperty
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
    table_ref: OdxLinkRef
    key_raw: str
    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]
    dop_ref: Optional[OdxLinkRef]
    dop_snref: Optional[str]
    description: Optional[str]
    semantic: Optional[str]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self) -> None:
        self._structure: Optional[BasicStructure] = None
        self._dop: Optional[DataObjectProperty] = None

        n = sum([0 if x is None else 1 for x in (self.structure_ref, self.structure_snref)])
        assert n <= 1, f"Table row {self.short_name}: The structure can either be defined using ODXLINK or SNREF but not both."
        n = sum([0 if x is None else 1 for x in (self.dop_ref, self.dop_snref)])
        assert n <= 1, f"Table row {self.short_name}: The dop can either be defined using ODXLINK or SNREF but not both."

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment], *,
                table_ref: OdxLinkRef) -> "TableRow":
        """Reads a TABLE-ROW."""
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        semantic = et_element.get("SEMANTIC")
        description = create_description_from_et(et_element.find("DESC"))
        key_raw = et_element.findtext("KEY")
        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        structure_snref: Optional[str] = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = structure_snref_elem.attrib["SHORT-NAME"]
        dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags)
        dop_snref: Optional[str] = None
        if (dop_snref_elem := et_element.find("DATA-OBJECT-PROP-SNREF")) is not None:
            dop_snref = dop_snref_elem.attrib["SHORT-NAME"]
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return TableRow(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            table_ref=table_ref,
            semantic=semantic,
            description=description,
            key_raw=key_raw,
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref, BasicStructure)
        if self.dop_ref is not None:
            self._dop = odxlinks.resolve(self.dop_ref, DataObjectProperty)

        self._table = odxlinks.resolve(self.table_ref)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        # convert the raw key into the proper internal
        # representation. note that we cannot do this earlier because
        # the table's ODXLINKs must be resolved and the order of
        # ODXLINK resolution between tables and table-rows is
        # undefined.
        key_dop = self.table.key_dop
        self._key: AtomicOdxType
        if key_dop is None:
            # if the table does not define a DOP for the keys: though
            # luck, expose the raw key string. This is probably a gap
            # in the ODX specification because table-rows must exhibit
            # a "KEY" sub-tag, while the KEY-DOP-REF is optional for
            # tables (and non-existant for table rows...)
            self._key = self.key_raw
        else:
            self._key = key_dop.physical_type.base_data_type.from_string(self.key_raw)

        ddd_spec = diag_layer.diag_data_dictionary_spec

        if self.structure_snref is not None:
            self._structure = ddd_spec.structures[self.structure_snref]
        if self.dop_snref is not None:
            self._dop = ddd_spec.data_object_props[self.dop_snref]

        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

    @property
    def table(self) -> "Table":
        return self._table

    # the value of the key expressed in the type represented by the
    # referenced DOP
    @property
    def key(self) -> Optional[AtomicOdxType]:
        return self._key

    @property
    def structure(self) -> Optional[BasicStructure]:
        """The structure associated with this table row."""
        return self._structure

    @property
    def dop(self) -> Optional[DataObjectProperty]:
        """The data object property object resolved by dop_ref."""
        return self._dop

    def __repr__(self) -> str:
        return (f"TableRow('{self.short_name}', " + ", ".join([
            f"key='{str(self.key)}'",
            f"structure_ref='{self.structure_ref}'",
            f"dop_ref='{self.dop_ref}'",
        ]) + ")")
