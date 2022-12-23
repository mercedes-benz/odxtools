# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Iterable

from .utils import create_description_from_et
from .odxlink import OdxLinkRef, OdxLinkId, OdxLinkDatabase, OdxDocFragment

from .dataobjectproperty import DopBase
from .globals import logger
from .specialdata import SpecialDataGroup, create_sdgs_from_et


class TableBase(abc.ABC):
    """ Base class for all Tables."""

    def __init__(self,
                 odx_id: OdxLinkId,
                 short_name: str,
                 long_name=None,
                 sdgs: List[SpecialDataGroup] = []):
        self.odx_id = odx_id
        self.short_name = short_name
        self.long_name = long_name
        self.sdgs = sdgs

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

@dataclass
class TableRow:
    """This class represents a TABLE-ROW."""

    odx_id: OdxLinkId
    short_name: str
    long_name: str
    key: int
    structure_ref: Optional[OdxLinkRef] = None
    dop_ref: Optional[OdxLinkRef] = None
    description: Optional[str] = None
    semantic: Optional[str] = None
    sdgs: List[SpecialDataGroup] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._structure: Optional[DopBase] = None
        self._dop: Optional[DopBase] = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "TableRow":
        """Reads a TABLE-ROW."""
        odx_id=OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name=et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name=et_element.findtext("LONG-NAME")
        semantic=et_element.get("SEMANTIC")
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
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)
        if self.dop_ref is not None:
            self._dop = odxlinks.resolve(self.dop_ref)

        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

    @property
    def structure(self) -> Optional[DopBase]:
        """The structure associated with this table row."""
        return self._structure

    @property
    def dop(self) -> Optional[DopBase]:
        """The dop object resolved by dop_ref."""
        return self._dop

    def __repr__(self) -> str:
        return (
            f"TableRow('{self.short_name}', "
            + ", ".join(
                [
                    f"key='{self.key}'",
                    f"structure_ref='{self.structure_ref}'",
                    f"dop_ref='{self.dop_ref}'",
                ]
            )
            + ")"
        )

class Table(TableBase):
    """This class represents a TABLE."""

    def __init__(
        self,
        odx_id: OdxLinkId,
        short_name: str,
        table_rows: List[TableRow],
        table_row_refs: Optional[List[OdxLinkRef]] = None,
        long_name: Optional[str] = None,
        key_dop_ref: Optional[OdxLinkRef] = None,
        description: Optional[str] = None,
        semantic: Optional[str] = None,
        sdgs: List[SpecialDataGroup] = [],
    ):
        super().__init__(odx_id=odx_id,
                         short_name=short_name,
                         long_name=long_name,
                         sdgs = sdgs,
                         )
        self._local_table_rows = table_rows
        self._ref_table_rows: List[TableRow] = []
        self._table_row_refs = table_row_refs or []
        self.key_dop_ref = key_dop_ref
        self._key_dop = None
        self.description = description
        self.semantic = semantic

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "Table":
        """Reads a TABLE."""
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        semantic = et_element.get("SEMANTIC")
        description = create_description_from_et(et_element.find("DESC"))
        key_dop_ref = None
        if et_element.find("KEY-DOP-REF") is not None:
            key_dop_ref = OdxLinkRef.from_et(et_element.find("KEY-DOP-REF"), doc_frags)
        logger.debug("Parsing TABLE " + short_name)

        table_rows = [
            TableRow.from_et(tr_elem, doc_frags)
            for tr_elem in et_element.iterfind("TABLE-ROW")
        ]

        table_row_refs = [ ]
        for el in et_element.iterfind("TABLE-ROW-REF"):
            ref = OdxLinkRef.from_et(el, doc_frags)
            assert ref is not None
            table_row_refs.append(ref)
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return Table(odx_id=odx_id,
                     short_name=short_name,
                     long_name=long_name,
                     semantic=semantic,
                     description=description,
                     key_dop_ref=key_dop_ref,
                     table_rows=table_rows,
                     table_row_refs=table_row_refs,
                     sdgs=sdgs,
                     )

    @property
    def key_dop(self) -> Optional[DopBase]:
        """The key data object property associated with this table."""
        return self._key_dop

    @property
    def table_rows(self) -> Iterable[TableRow]:
        """The table rows (both local and referenced) in this table."""
        return self._local_table_rows + self._ref_table_rows

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for tr in self._local_table_rows:
            result.update(tr._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_references(odxlinks)

        if self.key_dop_ref is not None:
            self._key_dop = odxlinks.resolve(self.key_dop_ref)

        for table_row in self._local_table_rows:
            table_row._resolve_references(odxlinks)

        self._ref_table_rows = []
        for ref in self._table_row_refs:
            tr = odxlinks.resolve(ref)
            assert isinstance(tr, TableRow)
            self._ref_table_rows.append(tr)

    def __repr__(self) -> str:
        return (
            f"Table('{self.short_name}', "
            + ", ".join(
                [f"table_rows='{self.table_rows}'", f"key_dop_ref='{self.key_dop_ref}'"]
            )
            + ")"
        )

