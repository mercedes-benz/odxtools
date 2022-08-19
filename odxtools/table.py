# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Iterable

from odxtools.utils import read_description_from_odx

from .dataobjectproperty import DopBase
from .globals import logger


class TableBase(abc.ABC):
    """ Base class for all Tables."""

    def __init__(self, id: str, short_name: str, long_name=None):
        self.id = id
        self.short_name = short_name
        self.long_name = long_name


@dataclass
class TableRow:
    """This class represents a TABLE-ROW."""

    id: str
    short_name: str
    long_name: str
    key: int
    structure_ref: Optional[str] = None
    dop_ref: Optional[str] = None
    description: Optional[str] = None
    semantic: Optional[str] = None

    def __post_init__(self):
        self._structure: Optional[DopBase] = None
        self._dop: Optional[DopBase] = None

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        if self.structure_ref is not None:
            self._structure = id_lookup.get(self.structure_ref)
            if self._structure is None:
                logger.warning(
                    f"STRUCTURE-REF '{self.structure_ref}' could not be resolved in TABLE-ROW."
                )
        if self.dop_ref is not None:
            self._dop = id_lookup.get(self.dop_ref)
            if self._dop is None:
                logger.warning(
                    f"DATA-OBJECT-PROP-REF '{self.dop_ref}' could not be resolved in TABLE-ROW."
                )

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
        id: str,
        short_name: str,
        table_rows: List[TableRow],
        table_row_refs: Optional[List[str]] = None,
        long_name: Optional[str] = None,
        key_dop_ref: Optional[str] = None,
        description: Optional[str] = None,
        semantic: Optional[str] = None,
    ):
        super().__init__(
            id=id, short_name=short_name, long_name=long_name
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

    def _build_id_lookup(self):
        id_lookup = {}
        id_lookup.update({table_row.id: table_row for table_row in self.table_rows})
        return id_lookup

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        if self.key_dop_ref is not None:
            self._key_dop = id_lookup.get(self.key_dop_ref)
            if self._key_dop is None:
                logger.warning(
                    f"KEY-DOP-REF '{self.key_dop_ref!r}' could not be resolved in TABLE."
                )
        for table_row in self._local_table_rows:
            table_row._resolve_references(id_lookup)

        self._ref_table_rows = []
        for ref in self._table_row_refs:
            tr = id_lookup.get(ref)
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


def _get_common_props(et_element):
    description = read_description_from_odx(et_element.find("DESC"))
    return dict(
        id=et_element.get("ID"),
        short_name=et_element.findtext("SHORT-NAME"),
        long_name=et_element.findtext("LONG-NAME"),
        semantic=et_element.get("SEMANTIC"),
        description=description,
    )


def read_table_row_from_odx(et_element):
    """Reads a TABLE-ROW."""
    key = et_element.find("KEY").text
    structure_ref = None
    if et_element.find("STRUCTURE-REF") is not None:
        structure_ref = et_element.find("STRUCTURE-REF").get("ID-REF")
    dop_ref = None
    if et_element.find("DATA-OBJECT-PROP-REF") is not None:
        dop_ref = et_element.find("DATA-OBJECT-PROP-REF").get("ID-REF")

    table_row = TableRow(
        key=key,
        structure_ref=structure_ref,
        dop_ref=dop_ref,
        **_get_common_props(et_element)
    )

    return table_row


def read_table_from_odx(et_element):
    """Reads a TABLE."""
    short_name = et_element.find("SHORT-NAME").text
    key_dop_ref = None
    if et_element.find("KEY-DOP-REF") is not None:
        key_dop_ref = et_element.find("KEY-DOP-REF").get("ID-REF")
    logger.debug("Parsing TABLE " + short_name)

    table_rows = [
        read_table_row_from_odx(el) for el in et_element.iterfind("TABLE-ROW")
    ]

    table_row_refs = [
        el.get('ID-REF') for el in et_element.iterfind("TABLE-ROW-REF")
    ]

    table = Table(
        key_dop_ref=key_dop_ref,
        table_rows=table_rows,
        table_row_refs=table_row_refs,
        **_get_common_props(et_element)
    )

    return table
