# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .element import IdentifiableElement
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class FunctionalClass(IdentifiableElement):
    """
    Corresponds to FUNCT-CLASS.
    """

    admin_data: AdminData | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "FunctionalClass":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)

        return FunctionalClass(admin_data=admin_data, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
