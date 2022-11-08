# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Iterable

from .utils import read_description_from_odx
from .odxlink import OdxLinkRef, OdxLinkId, OdxLinkDatabase, OdxDocFragment

from .dataobjectproperty import DopBase
from .globals import logger


class TableBase(abc.ABC):
    """ Base class for all Tables."""

    def __init__(self, odx_id: OdxLinkId, short_name: str, long_name=None):
        self.odx_id = odx_id
        self.short_name = short_name
        self.long_name = long_name


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

    def __post_init__(self) -> None:
        self._structure: Optional[DopBase] = None
        self._dop: Optional[DopBase] = None

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref)
        if self.dop_ref is not None:
            self._dop = odxlinks.resolve(self.dop_ref)

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
    ):
        super().__init__(
            odx_id=odx_id, short_name=short_name, long_name=long_name
        )
        self._local_table_rows = table_rows
        self._ref_table_rows: List[TableRow] = []
        self._table_row_refs = table_row_refs or []
        self.key_dop_ref = key_dop_ref
        self._key_dop = None
        self.description = description
        self.semantic = semantic

    @property
    def key_dop(self) -> Optional[DopBase]:
        """The key data object property associated with this table."""
        return self._key_dop

    @property
    def table_rows(self) -> Iterable[TableRow]:
        """The table rows (both local and referenced) in this table."""
        return self._local_table_rows + self._ref_table_rows

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {}
        odxlinks.update({table_row.odx_id: table_row for table_row in self.table_rows})
        return odxlinks

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        if self.key_dop_ref is not None:
            self._key_dop = odxlinks.resolve(self.key_dop_ref)

        for table_row in self._local_table_rows:
            table_row._resolve_references(odxlinks)

        self._ref_table_rows = []
        for ref in self._table_row_refs:
            tr = odxlinks.resolve(ref)
            if isinstance(tr, TableRow):
                self._ref_table_rows.append(tr)

    def __repr__(self) -> str:
        return (
            f"Table('{self.short_name}', "
            + ", ".join(
                [f"table_rows='{self.table_rows}'", f"key_dop_ref='{self.key_dop_ref}'"]
            )
            + ")"
        )


def _get_common_props(et_element, doc_frags: List[OdxDocFragment]):
    description = read_description_from_odx(et_element.find("DESC"))
    return dict(
        odx_id=OdxLinkId.from_et(et_element, doc_frags),
        short_name=et_element.findtext("SHORT-NAME"),
        long_name=et_element.findtext("LONG-NAME"),
        semantic=et_element.get("SEMANTIC"),
        description=description,
    )


def read_table_row_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
    -> TableRow:
    """Reads a TABLE-ROW."""
    key = et_element.find("KEY").text
    structure_ref = None
    if et_element.find("STRUCTURE-REF") is not None:
        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
    dop_ref = None
    if et_element.find("DATA-OBJECT-PROP-REF") is not None:
        dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags)

    return TableRow(
        key=key,
        structure_ref=structure_ref,
        dop_ref=dop_ref,
        **_get_common_props(et_element, doc_frags)
    )


def read_table_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
    -> Table:
    """Reads a TABLE."""
    short_name = et_element.find("SHORT-NAME").text
    key_dop_ref = None
    if et_element.find("KEY-DOP-REF") is not None:
        key_dop_ref = OdxLinkRef.from_et(et_element.find("KEY-DOP-REF"), doc_frags)
    logger.debug("Parsing TABLE " + short_name)

    table_rows = [
        read_table_row_from_odx(el, doc_frags) for el in et_element.iterfind("TABLE-ROW")
    ]

    table_row_refs = [ ]
    for el in et_element.iterfind("TABLE-ROW-REF"):
        ref = OdxLinkRef.from_et(el, doc_frags)
        assert ref is not None
        table_row_refs.append(ref)

    return Table(
        key_dop_ref=key_dop_ref,
        table_rows=table_rows,
        table_row_refs=table_row_refs,
        **_get_common_props(et_element, doc_frags)
    )
