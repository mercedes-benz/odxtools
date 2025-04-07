# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .diagclasstype import DiagClassType
from .diagcomm import DiagComm
from .exceptions import odxassert, odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext
from .table import Table


@dataclass(kw_only=True)
class DynIdDefModeInfo:
    def_mode: str

    clear_dyn_def_message_ref: OdxLinkRef | None = None
    clear_dyn_def_message_snref: str | None = None

    read_dyn_def_message_ref: OdxLinkRef | None = None
    read_dyn_def_message_snref: str | None = None

    dyn_def_message_ref: OdxLinkRef | None = None
    dyn_def_message_snref: str | None = None

    supported_dyn_ids: list[bytes] = field(default_factory=list)
    selection_table_refs: list[OdxLinkRef | str] = field(default_factory=list)

    @property
    def clear_dyn_def_message(self) -> DiagComm:
        return self._clear_dyn_def_message

    @property
    def read_dyn_def_message(self) -> DiagComm:
        return self._read_dyn_def_message

    @property
    def dyn_def_message(self) -> DiagComm:
        return self._dyn_def_message

    @property
    def selection_tables(self) -> NamedItemList[Table]:
        return self._selection_tables

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DynIdDefModeInfo":
        def_mode = odxrequire(et_element.findtext("DEF-MODE"))

        clear_dyn_def_message_ref = OdxLinkRef.from_et(
            et_element.find("CLEAR-DYN-DEF-MESSAGE-REF"), context)
        clear_dyn_def_message_snref = None
        if (snref_elem := et_element.find("CLEAR-DYN-DEF-MESSAGE-SNREF")) is not None:
            clear_dyn_def_message_snref = odxrequire(snref_elem.attrib.get("SHORT-NAME"))

        read_dyn_def_message_ref = OdxLinkRef.from_et(
            et_element.find("READ-DYN-DEF-MESSAGE-REF"), context)
        read_dyn_def_message_snref = None
        if (snref_elem := et_element.find("READ-DYN-DEF-MESSAGE-SNREF")) is not None:
            read_dyn_def_message_snref = odxrequire(snref_elem.attrib.get("SHORT-NAME"))

        dyn_def_message_ref = OdxLinkRef.from_et(et_element.find("DYN-DEF-MESSAGE-REF"), context)
        dyn_def_message_snref = None
        if (snref_elem := et_element.find("DYN-DEF-MESSAGE-SNREF")) is not None:
            dyn_def_message_snref = odxrequire(snref_elem.attrib.get("SHORT-NAME"))

        supported_dyn_ids = [
            bytes.fromhex(odxrequire(x.text))
            for x in et_element.iterfind("SUPPORTED-DYN-IDS/SUPPORTED-DYN-ID")
        ]

        selection_table_refs: list[OdxLinkRef | str] = []
        if (st_elems := et_element.find("SELECTION-TABLE-REFS")) is not None:
            for st_elem in st_elems:
                if st_elem.tag == "SELECTION-TABLE-REF":
                    selection_table_refs.append(OdxLinkRef.from_et(st_elem, context))
                elif st_elem.tag == "SELECTION-TABLE-SNREF":
                    selection_table_refs.append(odxrequire(st_elem.get("SHORT-NAME")))
                else:
                    odxraise()

        return DynIdDefModeInfo(
            def_mode=def_mode,
            clear_dyn_def_message_ref=clear_dyn_def_message_ref,
            clear_dyn_def_message_snref=clear_dyn_def_message_snref,
            read_dyn_def_message_ref=read_dyn_def_message_ref,
            read_dyn_def_message_snref=read_dyn_def_message_snref,
            dyn_def_message_ref=dyn_def_message_ref,
            dyn_def_message_snref=dyn_def_message_snref,
            supported_dyn_ids=supported_dyn_ids,
            selection_table_refs=selection_table_refs,
        )

    def __post_init__(self) -> None:
        odxassert(
            self.clear_dyn_def_message_ref is not None or
            self.clear_dyn_def_message_snref is not None,
            "A CLEAR-DYN-DEF-MESSAGE must be specified")
        odxassert(
            self.read_dyn_def_message_ref is not None or
            self.read_dyn_def_message_snref is not None, "A READ-DYN-DEF-MESSAGE must be specified")
        odxassert(self.dyn_def_message_ref is not None or self.dyn_def_message_snref is not None,
                  "A DYN-DEF-MESSAGE must be specified")

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result: dict[OdxLinkId, Any] = {}

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.clear_dyn_def_message_ref is not None:
            self._clear_dyn_def_message = odxlinks.resolve(self.clear_dyn_def_message_ref, DiagComm)

        if self.read_dyn_def_message_ref is not None:
            self._read_dyn_def_message = odxlinks.resolve(self.read_dyn_def_message_ref, DiagComm)

        if self.dyn_def_message_ref is not None:
            self._dyn_def_message = odxlinks.resolve(self.dyn_def_message_ref, DiagComm)

        # resolve the selection tables that are referenced via ODXLINK
        self._selection_tables = NamedItemList[Table]()
        for x in self.selection_table_refs:
            if isinstance(x, OdxLinkRef):
                self._selection_tables.append(odxlinks.resolve(x, Table))

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        diag_layer = odxrequire(context.diag_layer)

        if self.clear_dyn_def_message_snref is not None:
            self._clear_dyn_def_message = resolve_snref(self.clear_dyn_def_message_snref,
                                                        diag_layer.diag_comms, DiagComm)

        if self.read_dyn_def_message_snref is not None:
            self._read_dyn_def_message = resolve_snref(self.read_dyn_def_message_snref,
                                                       diag_layer.diag_comms, DiagComm)

        if self.dyn_def_message_snref is not None:
            self._dyn_def_message = resolve_snref(self.dyn_def_message_snref, diag_layer.diag_comms,
                                                  DiagComm)

        if self._clear_dyn_def_message.diagnostic_class != DiagClassType.CLEAR_DYN_DEF_MESSAGE:
            odxraise(
                f"Diagnostic communication object of wrong type referenced: "
                f"({odxrequire(self._clear_dyn_def_message.diagnostic_class).value} instead of "
                f"CLEAR-DYN-DEF-MESSAGE)")
        if self._read_dyn_def_message.diagnostic_class != DiagClassType.READ_DYN_DEFINED_MESSAGE:
            odxraise(f"Diagnostic communication object of wrong type referenced: "
                     f"({odxrequire(self._read_dyn_def_message.diagnostic_class).value} instead of "
                     f"READ-DYN-DEFINED-MESSAGE)")
        if self._dyn_def_message.diagnostic_class != DiagClassType.DYN_DEF_MESSAGE:
            odxraise(f"Diagnostic communication object of wrong type referenced: "
                     f"({odxrequire(self._dyn_def_message.diagnostic_class).value} instead of "
                     f"DYN-DEF-MESSAGE)")

        # resolve the remaining selection tables that are referenced via SNREF
        ddd_spec = odxrequire(diag_layer.diag_data_dictionary_spec)
        for i, x in enumerate(self.selection_table_refs):
            if isinstance(x, str):
                self._selection_tables.insert(i, resolve_snref(x, ddd_spec.tables, Table))
