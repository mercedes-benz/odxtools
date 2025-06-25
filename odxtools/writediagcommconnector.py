# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .parameters.valueparameter import ValueParameter
from .request import Request
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class WriteDiagCommConnector:
    # exactly one of the following attributes must be non-None
    write_diag_comm_ref: OdxLinkRef | None = None
    write_diag_comm_snref: str | None = None

    # exactly one of the following attributes must be non-None
    write_data_snref: str | None = None
    write_data_snpathref: str | None = None

    @property
    def write_diag_comm(self) -> DiagComm | None:
        return self._write_diag_comm

    @property
    def write_data(self) -> ValueParameter | None:
        return self._write_data

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "WriteDiagCommConnector":
        write_diag_comm_ref = OdxLinkRef.from_et(et_element.find("WRITE-DIAG-COMM-REF"), context)
        write_diag_comm_snref = None
        if (write_diag_comm_snref_elem := et_element.find("WRITE-DIAG-COMM-SNREF")) is not None:
            write_diag_comm_snref = odxrequire(write_diag_comm_snref_elem.attrib.get("SHORT-NAME"))

        write_data_snref = None
        if (write_data_snref_elem := et_element.find("WRITE-DATA-SNREF")) is not None:
            write_data_snref = odxrequire(write_data_snref_elem.attrib.get("SHORT-NAME"))

        write_data_snpathref = None
        if (write_data_snpathref_elem := et_element.find("WRITE-DATA-SNPATHREF")) is not None:
            write_data_snpathref = odxrequire(
                write_data_snpathref_elem.attrib.get("SHORT-NAME-PATH"))

        return WriteDiagCommConnector(
            write_diag_comm_ref=write_diag_comm_ref,
            write_diag_comm_snref=write_diag_comm_snref,
            write_data_snref=write_data_snref,
            write_data_snpathref=write_data_snpathref,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._write_diag_comm = None
        if self.write_diag_comm_ref is not None:
            self._write_diag_comm = odxlinks.resolve(self.write_diag_comm_ref, DiagComm)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # write_diag_comm_snref can only be uniquely resolved ahead of
        # time if the diag comm is referenced via ODXLINK, the write
        # data parameter is referenced via SNREF. If the diag comm is
        # referenced via SNREF, it depends on the applicable diag layer
        self._write_data = None
        if self.write_data_snref is not None and \
           self._write_diag_comm is not None and \
           (req := getattr(self._write_diag_comm, "request", None)) is not None:
            assert isinstance(req, Request)
            self._write_data = resolve_snref(self.write_data_snref, req.parameters, ValueParameter)
