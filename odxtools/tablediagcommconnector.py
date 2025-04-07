# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class TableDiagCommConnector:
    semantic: str

    diag_comm_ref: OdxLinkRef | None = None
    diag_comm_snref: str | None = None

    @property
    def diag_comm(self) -> DiagComm:
        return self._diag_comm

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "TableDiagCommConnector":

        semantic = odxrequire(et_element.findtext("SEMANTIC"))

        diag_comm_ref = OdxLinkRef.from_et(et_element.find("DIAG-COMM-REF"), context)
        diag_comm_snref = None
        if (dc_snref_elem := et_element.find("DIAG-COMM-SNREF")) is not None:
            diag_comm_snref = odxrequire(dc_snref_elem.get("SHORT-NAME"))

        return TableDiagCommConnector(
            semantic=semantic, diag_comm_ref=diag_comm_ref, diag_comm_snref=diag_comm_snref)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.diag_comm_ref is not None:
            self._diag_comm = odxlinks.resolve(self.diag_comm_ref, DiagComm)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.diag_comm_snref is not None:
            dl = odxrequire(context.diag_layer)
            self._diag_comm = resolve_snref(self.diag_comm_snref, dl.diag_comms, DiagComm)
