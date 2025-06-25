# SPDX-License-Identifier: MIT
import re
from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from bincopy import BinFile

from .dataformat import Dataformat
from .dataformatselection import DataformatSelection
from .element import IdentifiableElement
from .encryptcompressmethod import EncryptCompressMethod
from .exceptions import odxassert, odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class Flashdata(IdentifiableElement):
    size_length: int | None = None
    address_length: int | None = None
    dataformat: Dataformat
    encrypt_compress_method: EncryptCompressMethod | None = None

    @property
    def data_str(self) -> str:
        raise NotImplementedError(f"The .data_str property has not been implemented "
                                  f"by the {type(self).__name__} class")

    @property
    def dataset(self) -> BinFile | bytearray | None:
        data_str = self.data_str
        if self.dataformat.selection in (DataformatSelection.INTEL_HEX,
                                         DataformatSelection.MOTOROLA_S):
            bf = BinFile()

            # remove white space and empty lines
            bf.add("\n".join([re.sub(r"\s", "", x) for x in data_str.splitlines() if x.strip()]))

            return bf
        elif self.dataformat.selection == DataformatSelection.BINARY:
            return bytearray.fromhex(re.sub(r"\s", "", data_str, flags=re.MULTILINE))
        else:
            odxassert(self.dataformat.selection == DataformatSelection.USER_DEFINED,
                      f"Unsupported data format {self.dataformat.selection}")
            return None

    @property
    def blob(self) -> bytearray:
        ds = self.dataset
        if isinstance(ds, BinFile):
            return cast(bytearray, ds.as_binary())
        elif isinstance(ds, bytearray):
            return ds

        odxraise("USER-DEFINED flash data cannot be interpreted on the odxtools level")
        return bytearray()

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Flashdata":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        size_length = None
        if (size_length_str := et_element.findtext("SIZE-LENGTH")) is not None:
            size_length = int(size_length_str)

        address_length = None
        if (address_length_str := et_element.findtext("ADDRESS-LENGTH")) is not None:
            address_length = int(address_length_str)

        dataformat = Dataformat.from_et(odxrequire(et_element.find("DATAFORMAT")), context)

        encrypt_compress_method = None
        if (encrypt_compress_method_elem := et_element.find("ENCRYPT-COMPRESS-METHOD")) is not None:
            encrypt_compress_method = EncryptCompressMethod.from_et(encrypt_compress_method_elem,
                                                                    context)

        return Flashdata(
            size_length=size_length,
            address_length=address_length,
            dataformat=dataformat,
            encrypt_compress_method=encrypt_compress_method,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        if self.dataformat is not None:
            odxlinks.update(self.dataformat._build_odxlinks())
        if self.encrypt_compress_method is not None:
            odxlinks.update(self.encrypt_compress_method._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.dataformat is not None:
            self.dataformat._resolve_odxlinks(odxlinks)
        if self.encrypt_compress_method is not None:
            self.encrypt_compress_method._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.dataformat is not None:
            self.dataformat._resolve_snrefs(context)
        if self.encrypt_compress_method is not None:
            self.encrypt_compress_method._resolve_snrefs(context)
