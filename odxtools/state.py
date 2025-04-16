# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import IdentifiableElement
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class State(IdentifiableElement):
    """
    Corresponds to STATE.
    """

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "State":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        return State(**kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
