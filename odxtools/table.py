# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .dataobjectproperty import DopBase
from .globals import logger


class TableBase(abc.ABC):
    """ Base class for all Tables."""

    def __init__(self, id: str, short_name: str, key_dop_ref: str, long_name=None):
        self.id = id
        self.short_name = short_name
        self.long_name = long_name
        self.key_dop_ref = key_dop_ref


@dataclass
class TableRow:
    """This class represents a TABLE-ROW."""

    id: str
    short_name: str
    long_name: str
    key: int
    structure_ref: str

    def __post_init__(self):
        self._structure: Optional[DopBase] = None

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        self._structure = id_lookup.get(self.structure_ref)
        if self._structure is None:
            logger.warning(
                f"STRUCTURE-REF '{self.structure_ref!r}' could not be resolved."
            )

    @property
    def structure(self) -> Optional[DopBase]:
        """The structure associated with this table row."""
        return self._structure

    def __repr__(self) -> str:
        return (
            f"TableRow('{self.short_name}', "
            + ", ".join([f"key='{self.key}'", f"structure_ref='{self.structure_ref}'"])
            + ")"
        )


class Table(TableBase):
    """This class represents a TABLE."""

    def __init__(
        self,
        id: str,
        short_name: str,
        key_dop_ref: str,
        table_rows: List[TableRow],
        long_name: Optional[str] = None,
    ):
        super().__init__(
            id=id, short_name=short_name, long_name=long_name, key_dop_ref=key_dop_ref
        )
        self.table_rows = table_rows
        self._key_dop = None

    @property
    def key_dop(self) -> Optional[DopBase]:
        """The key data object property associated with this table."""
        return self._key_dop

    def _build_id_lookup(self):
        id_lookup = {}
        id_lookup.update({table_row.id: table_row for table_row in self.table_rows})
        return id_lookup

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        self._key_dop = id_lookup.get(self.key_dop_ref)
        if self._key_dop is None:
            logger.warning(f"KEY-DOP-REF '{self.key_dop_ref!r}' could not be resolved.")
        for table_row in self.table_rows:
            table_row._resolve_references(id_lookup)

    def __repr__(self) -> str:
        return (
            f"Table('{self.short_name}', "
            + ", ".join(
                [f"table_rows='{self.table_rows}'", f"key_dop_ref='{self.key_dop_ref}'"]
            )
            + ")"
        )


def read_table_row_from_odx(et_element):
    """Reads a TABLE-ROW."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME").text
    key = et_element.find("KEY").text
    structure_ref = ""
    if et_element.find("STRUCTURE-REF") is not None:
        structure_ref = et_element.find("STRUCTURE-REF").get("ID-REF")

    table_row = TableRow(
        id=id,
        short_name=short_name,
        long_name=long_name,
        key=key,
        structure_ref=structure_ref,
    )

    return table_row


def read_table_from_odx(et_element):
    """Reads a TABLE."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME").text
    key_dop_ref = ""
    if et_element.find("KEY-DOP-REF") is not None:
        key_dop_ref = et_element.find("KEY-DOP-REF").get("ID-REF")
    logger.debug("Parsing TABLE " + short_name)

    table_rows = [
        read_table_row_from_odx(el) for el in et_element.iterfind("TABLE-ROW")
    ]

    table = Table(
        id=id,
        short_name=short_name,
        long_name=long_name,
        key_dop_ref=key_dop_ref,
        table_rows=table_rows,
    )

    return table
