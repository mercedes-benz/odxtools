# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .exceptions import odxrequire
from .logicallink import LogicalLink
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class FunctionDiagCommConnector:
    logical_link_ref: OdxLinkRef | None = None
    diag_comm_ref: OdxLinkRef

    @property
    def logical_link(self) -> LogicalLink | None:
        return self._logical_link

    @property
    def diag_comm(self) -> DiagComm:
        return self._diag_comm

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "FunctionDiagCommConnector":
        logical_link_ref = None
        if (ll_elem := et_element.find("LOGICAL-LINK-REF")) is not None:
            logical_link_ref = OdxLinkRef.from_et(ll_elem, context)

        diag_comm_ref = OdxLinkRef.from_et(odxrequire(et_element.find("DIAG-COMM-REF")), context)

        return FunctionDiagCommConnector(
            logical_link_ref=logical_link_ref, diag_comm_ref=diag_comm_ref)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._logical_link = None
        if self.logical_link_ref is not None:
            self._logical_link = odxlinks.resolve(self.logical_link_ref, LogicalLink)

        self._diag_comm = odxlinks.resolve(self.diag_comm_ref, DiagComm)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
