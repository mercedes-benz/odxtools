# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxrequire
from .identvalue import IdentValue
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class OwnIdent(IdentifiableElement):
    """
    Corresponds to OWN-IDENT.
    """

    ident_value: IdentValue

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "OwnIdent":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        ident_value = IdentValue.from_et(odxrequire(et_element.find("IDENT-VALUE")), context)

        return OwnIdent(ident_value=ident_value, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
