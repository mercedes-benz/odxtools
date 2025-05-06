# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .encryptcompressmethod import EncryptCompressMethod
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class Segment(IdentifiableElement):
    source_start_address: int
    compressed_size: int | None = None

    # exactly one of the two next fields must be not None
    uncompressed_size: int | None = None
    source_end_address: int | None = None

    encrypt_compress_method: EncryptCompressMethod | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Segment":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        source_start_address = odxrequire(read_hex_binary(et_element.find("SOURCE-START-ADDRESS")))
        compressed_size = None
        if (cs_elem := et_element.find("COMPRESSED-SIZE")) is not None:
            compressed_size = int(odxrequire(cs_elem.text) or "0")

        # exactly one of the two next fields must be not None
        uncompressed_size = None
        if (ucs_elem := et_element.find("UNCOMPRESSED-SIZE")) is not None:
            uncompressed_size = int(odxrequire(ucs_elem.text) or "0")
        source_end_address = read_hex_binary(et_element.find("SOURCE-END-ADDRESS"))

        encrypt_compress_method = None
        if (encrypt_compress_method_elem := et_element.find("ENCRYPT-COMPRESS-METHOD")) is not None:
            encrypt_compress_method = EncryptCompressMethod.from_et(encrypt_compress_method_elem,
                                                                    context)

        return Segment(
            source_start_address=source_start_address,
            compressed_size=compressed_size,
            uncompressed_size=uncompressed_size,
            source_end_address=source_end_address,
            encrypt_compress_method=encrypt_compress_method,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
