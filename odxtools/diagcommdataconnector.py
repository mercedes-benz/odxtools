# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .readdiagcommconnector import ReadDiagCommConnector
from .snrefcontext import SnRefContext
from .utils import read_hex_binary
from .writediagcommconnector import WriteDiagCommConnector


@dataclass(kw_only=True)
class DiagCommDataConnector:
    uncompressed_size: int
    source_start_address: int
    read_diag_comm_connector: ReadDiagCommConnector | None = None
    write_diag_comm_connector: WriteDiagCommConnector | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DiagCommDataConnector":
        uncompressed_size = int(odxrequire(et_element.findtext("UNCOMPRESSED-SIZE")))
        source_start_address = odxrequire(read_hex_binary(et_element.find("SOURCE-START-ADDRESS")))

        read_diag_comm_connector = None
        if (rdcc_elem := et_element.find("READ-DIAG-COMM-CONNECTOR")) is not None:
            read_diag_comm_connector = ReadDiagCommConnector.from_et(rdcc_elem, context)

        write_diag_comm_connector = None
        if (wdcc_elem := et_element.find("WRITE-DIAG-COMM-CONNECTOR")) is not None:
            write_diag_comm_connector = WriteDiagCommConnector.from_et(wdcc_elem, context)

        return DiagCommDataConnector(
            uncompressed_size=uncompressed_size,
            source_start_address=source_start_address,
            read_diag_comm_connector=read_diag_comm_connector,
            write_diag_comm_connector=write_diag_comm_connector)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {}

        if self.read_diag_comm_connector is not None:
            odxlinks.update(self.read_diag_comm_connector._build_odxlinks())
        if self.write_diag_comm_connector is not None:
            odxlinks.update(self.write_diag_comm_connector._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.read_diag_comm_connector is not None:
            self.read_diag_comm_connector._resolve_odxlinks(odxlinks)
        if self.write_diag_comm_connector is not None:
            self.write_diag_comm_connector._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.read_diag_comm_connector is not None:
            self.read_diag_comm_connector._resolve_snrefs(context)
        if self.write_diag_comm_connector is not None:
            self.write_diag_comm_connector._resolve_snrefs(context)
