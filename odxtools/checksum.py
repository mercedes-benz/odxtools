# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .checksumresult import ChecksumResult
from .element import IdentifiableElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class Checksum(IdentifiableElement):
    fillbyte: int | None = None
    source_start_address: int
    compressed_size: int | None = None
    checksum_alg: str | None = None

    # exactly one of the two next fields must be not None
    source_end_address: int | None = None
    uncompressed_size: int | None = None

    checksum_result: ChecksumResult

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Checksum":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        fillbyte = read_hex_binary(et_element.find("FILLBYTE"))
        source_start_address = odxrequire(read_hex_binary(et_element.find("SOURCE-START-ADDRESS")))
        compressed_size = None
        if (cs_elem := et_element.find("COMPRESSED-SIZE")) is not None:
            compressed_size = int(odxrequire(cs_elem.text) or "0")
        checksum_alg = et_element.findtext("CHECKSUM-ALG")

        # exactly one of the two next fields must be not None
        source_end_address = read_hex_binary(et_element.find("SOURCE-END-ADDRESS"))
        uncompressed_size = None
        if (ucs_elem := et_element.find("UNCOMPRESSED-SIZE")) is not None:
            uncompressed_size = int(odxrequire(ucs_elem.text) or "0")
        checksum_result = ChecksumResult.from_et(
            odxrequire(et_element.find("CHECKSUM-RESULT")), context)

        return Checksum(
            fillbyte=fillbyte,
            source_start_address=source_start_address,
            compressed_size=compressed_size,
            checksum_alg=checksum_alg,
            source_end_address=source_end_address,
            uncompressed_size=uncompressed_size,
            checksum_result=checksum_result,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
