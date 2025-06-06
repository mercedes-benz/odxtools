# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .readparamvalue import ReadParamValue
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class ReadDiagCommConnector:
    read_param_values: list[ReadParamValue]

    # exactly one of the following attributes must be non-None
    read_diag_comm_ref: OdxLinkRef | None = None
    read_diag_comm_snref: str | None = None

    # exactly one of the following attributes must be non-None
    read_data_snref: str | None = None
    read_data_snpathref: str | None = None

    @property
    def read_diag_comm(self) -> DiagComm | None:
        return self._read_diag_comm

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ReadDiagCommConnector":
        read_param_values = [
            ReadParamValue.from_et(el, context)
            for el in et_element.iterfind("READ-PARAM-VALUES/READ-PARAM-VALUE")
        ]

        read_diag_comm_ref = OdxLinkRef.from_et(et_element.find("READ-DIAG-COMM-REF"), context)
        read_diag_comm_snref = None
        if (read_diag_comm_snref_elem := et_element.find("READ-DIAG-COMM-SNREF")) is not None:
            read_diag_comm_snref = odxrequire(read_diag_comm_snref_elem.attrib.get("SHORT-NAME"))

        read_data_snref = None
        if (read_data_snref_elem := et_element.find("READ-DATA-SNREF")) is not None:
            read_data_snref = odxrequire(read_data_snref_elem.attrib.get("SHORT-NAME"))

        read_data_snpathref = None
        if (read_data_snpathref_elem := et_element.find("READ-DATA-SNPATHREF")) is not None:
            read_data_snpathref = odxrequire(read_data_snpathref_elem.attrib.get("SHORT-NAME-PATH"))

        return ReadDiagCommConnector(
            read_param_values=read_param_values,
            read_diag_comm_ref=read_diag_comm_ref,
            read_diag_comm_snref=read_diag_comm_snref,
            read_data_snref=read_data_snref,
            read_data_snpathref=read_data_snpathref,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {}

        for rpv in self.read_param_values:
            odxlinks.update(rpv._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._read_diag_comm = None
        if self.read_diag_comm_ref is not None:
            self._read_diag_comm = odxlinks.resolve(self.read_diag_comm_ref, DiagComm)

        for rpv in self.read_param_values:
            rpv._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # read_diag_comm_snref cannot be uniquely resolved ahead of
        # time as it depends on the diag layer which is used

        for rpv in self.read_param_values:
            rpv._resolve_snrefs(context)
