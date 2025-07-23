# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .flashdata import Flashdata
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class InternFlashdata(Flashdata):
    data: str

    @property
    def data_str(self) -> str:
        return self.data

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "InternFlashdata":
        kwargs = dataclass_fields_asdict(Flashdata.from_et(et_element, context))

        data = odxrequire(et_element.findtext("DATA"))

        return InternFlashdata(data=data, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
