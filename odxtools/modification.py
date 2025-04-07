# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class Modification:
    change: str
    reason: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Modification":
        change = odxrequire(et_element.findtext("CHANGE"))
        reason = et_element.findtext("REASON")

        return Modification(change=change, reason=reason)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
