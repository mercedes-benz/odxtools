# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .datafile import Datafile
from .exceptions import odxrequire
from .flashdata import Flashdata
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ExternFlashdata(Flashdata):
    datafile: Datafile

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
