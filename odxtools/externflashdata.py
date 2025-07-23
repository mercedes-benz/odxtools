# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import IO, Any
from xml.etree import ElementTree

from .datafile import Datafile
from .exceptions import odxraise, odxrequire
from .flashdata import Flashdata
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ExternFlashdata(Flashdata):
    datafile: Datafile

    @property
    def data_str(self) -> str:
        if self._database is None:
            odxraise("No database object specified")
            return ""

        aux_file: IO[bytes] = odxrequire(self._database.auxiliary_files.get(self.datafile.value))
        if aux_file is None:
            return ""

        result = aux_file.read().decode()
        aux_file.seek(0)

        return result

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ExternFlashdata":
        kwargs = dataclass_fields_asdict(Flashdata.from_et(et_element, context))

        datafile = Datafile.from_et(odxrequire(et_element.find("DATAFILE")), context)

        return ExternFlashdata(datafile=datafile, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        # this is slightly hacky because we only remember the
        # applicable ODX database and do not resolve any SNREFs here
        self._database = context.database
