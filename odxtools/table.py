# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
from dataclasses import dataclass
from typing import Optional, List

from .dataobjectproperty import DataObjectProperty
from .globals import logger
from .structures import Structure


class TableBase(abc.ABC):
    """ Base class for all Tables."""

    def __init__(self,
                 id: str,
                 short_name: str,
                 key_dop_ref: str,
                 long_name=None):
        self.id = id
        self.short_name = short_name
        self.long_name = long_name
        self.key_dop_ref = key_dop_ref


@dataclass()
class TableRow:
    """This class represents a TABLE-ROW."""

    id: str
    short_name: str
    key: int
    structure_ref: Optional[str] = None
    long_name: str = None
    _structure: Structure = None

    @property
    def structure(self) -> Optional[Structure]:
        return self._structure

    def _resolve_references(self, id_lookup):
        """Resolves the reference to the STRUCTURE-REF"""
        if self.structure_ref:
            self._structure = id_lookup[self.structure_ref]


class Table(TableBase):
    """This class represents a TABLE."""

    def __init__(self,
                 id: str,
                 short_name: str,
                 key_dop_ref: str,
                 table_rows: List[TableRow],
                 long_name: Optional[str] = None):
        super().__init__(id=id,
                         short_name=short_name,
                         long_name=long_name,
                         key_dop_ref=key_dop_ref)
        self.table_rows = table_rows
        self._key_dop = None

    @property
    def key_dop(self) -> Optional[DataObjectProperty]:
        return self._key_dop

    def _resolve_references(self, id_lookup):
        """Resolves the reference to the KEY-DOP-REF"""
        if self.key_dop_ref:
            self._key_dop = id_lookup[self.key_dop_ref]

    def __repr__(self) -> str:
        return \
            f"Table('{self.short_name}', " + \
            ", ".join([
                f"table_rows='{self.table_rows}'",
                f"key_dop_ref='{self.key_dop_ref}'",
            ]) + \
            ")"

    def __str__(self) -> str:
        return \
            f"Table('{self.short_name}', " + \
            ", ".join([
                f"table_rows='{self.table_rows}'",
                f"key_dop_ref='{self.key_dop_ref}'",
            ]) + \
            ")"


def read_table_row_from_odx(et_element):
    """Reads a TABLE-ROW."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME").text
    key = et_element.find("KEY").text
    structure_ref = None
    if et_element.find("STRUCTURE-REF"):
        structure_ref = et_element.find("STRUCTURE-REF").get("ID-REF")

    table_row = TableRow(
        id=id,
        short_name=short_name,
        long_name=long_name,
        key=key,
        structure_ref=structure_ref
    )

    return table_row


def read_table_from_odx(et_element):
    """Reads a TABLE."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME").text
    key_dop_ref = et_element.find("KEY-DOP-REF").get("ID-REF")
    logger.debug('Parsing TABLE ' + short_name)

    table_rows = [read_table_row_from_odx(el)
                  for el in et_element.iterfind("TABLE-ROW")]

    table = Table(
        id=id,
        short_name=short_name,
        long_name=long_name,
        key_dop_ref=key_dop_ref,
        table_rows=table_rows
    )

    return table
