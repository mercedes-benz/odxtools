# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from odxtools.dataobjectproperty import DopBase
from .globals import logger


@dataclass
class Case:
    """This class represents a CASE."""

    short_name: str
    long_name: str
    structure_ref: str
    lower_limit: str
    upper_limit: str

    def __post_init__(self):
        self._structure: Optional[DopBase] = None

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        self._structure = id_lookup.get(self.structure_ref)
        if self._structure is None:
            logger.warning(
                f"STRUCTURE-REF '{self.structure_ref}' could not be resolved."
            )

    def __repr__(self) -> str:
        return (
            f"Case('{self.short_name}', "
            + ", ".join(
                [
                    f"lower_limit='{self.lower_limit}'",
                    f"upper_limit='{self.upper_limit}'",
                    f"structure_ref='{self.structure_ref}'",
                ]
            )
            + ")"
        )


@dataclass
class DefaultCase:
    """This class represents a DEFAULT-CASE."""

    short_name: str
    long_name: str
    structure_ref: str

    def __post_init__(self):
        self._structure: Optional[DopBase] = None

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        self._structure = id_lookup.get(self.structure_ref)
        if self._structure is None:
            logger.warning(
                f"STRUCTURE-REF '{self.structure_ref}' could not be resolved."
            )

    def __repr__(self) -> str:
        return (
            f"DefaultCase('{self.short_name}', "
            + ", ".join(
                [
                    f"structure_ref='{self.structure_ref}'",
                ]
            )
            + ")"
        )


@dataclass
class SwitchKey:
    """This class represents a SWITCH-KEY."""

    byte_position: int
    bit_position: int
    dop_ref: str

    def __post_init__(self):
        self._dop: Optional[DopBase] = None

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        self._dop = id_lookup.get(self.dop_ref)
        if self._dop is None:
            logger.warning(
                f"DATA-OBJECT-PROP-REF '{self.dop_ref}' could not be resolved."
            )

    def __repr__(self) -> str:
        return (
            f"SwitchKey("
            + ", ".join(
                [
                    f"byte_position='{self.byte_position}'",
                    f"bit_position='{self.bit_position}'",
                    f"dop_ref='{self.dop_ref}'",
                ]
            )
            + ")"
        )


@dataclass
class Mux:
    """This class represents a MUX."""

    id: str
    short_name: str
    long_name: str
    byte_position: int
    switch_key: SwitchKey
    default_case: DefaultCase
    cases: List[Case]

    def _build_id_lookup(self):
        id_lookup = {}
        id_lookup.update({self.id: self})
        return id_lookup

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        self.switch_key._resolve_references(id_lookup)
        self.default_case._resolve_references(id_lookup)
        for case in self.cases:
            case._resolve_references(id_lookup)

    def __repr__(self) -> str:
        return (
            f"Mux('{self.short_name}', "
            + ", ".join(
                [
                    f"id='{self.id}'",
                    f"byte_position='{self.byte_position}'",
                    f"switch_key='{self.switch_key}'",
                    f"default_case='{self.default_case}'",
                    f"cases='{self.cases}'",
                ]
            )
            + ")"
        )


def read_switch_key_from_odx(et_element):
    """Reads a SWITCH-KEY."""
    byte_position = (
        int(et_element.find("BYTE-POSITION").text)
        if et_element.find("BYTE-POSITION") is not None
        else None
    )
    bit_position = (
        int(et_element.find("BIT-POSITION").text)
        if et_element.find("BIT-POSITION") is not None
        else 0
    )
    dop_ref = et_element.find("DATA-OBJECT-PROP-REF").get("ID-REF")

    return SwitchKey(
        byte_position=byte_position,
        bit_position=bit_position,
        dop_ref=dop_ref,
    )


def read_default_case_from_odx(et_element):
    """Reads a DEFAULT-CASE."""
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text
    structure_ref = et_element.find("STRUCTURE-REF").get("ID-REF")

    return DefaultCase(
        short_name=short_name,
        long_name=long_name,
        structure_ref=structure_ref,
    )


def read_case_from_odx(et_element):
    """Reads a CASE."""
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text
    structure_ref = et_element.find("STRUCTURE-REF").get("ID-REF")
    lower_limit = et_element.find("LOWER-LIMIT").text
    upper_limit = et_element.find("UPPER-LIMIT").text

    return Case(
        short_name=short_name,
        long_name=long_name,
        structure_ref=structure_ref,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
    )


def read_mux_from_odx(et_element):
    """Reads a MUX."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text
    byte_position = (
        int(et_element.find("BYTE-POSITION").text)
        if et_element.find("BYTE-POSITION") is not None
        else None
    )
    switch_key = read_switch_key_from_odx(et_element.find("SWITCH-KEY"))
    default_case = read_default_case_from_odx(et_element.find("DEFAULT-CASE"))

    cases = None
    if et_element.find("CASES") is not None:
        cases = [
            read_case_from_odx(el) for el in et_element.find("CASES").iterfind("CASE")
        ]

    logger.debug("Parsing MUX " + short_name)

    mux = Mux(
        id=id,
        short_name=short_name,
        long_name=long_name,
        byte_position=byte_position,
        switch_key=switch_key,
        default_case=default_case,
        cases=cases,
    )

    return mux
