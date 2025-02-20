# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass
class Modification:
    change: str
    reason: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Modification":
        change = odxrequire(et_element.findtext("CHANGE"))
        reason = et_element.findtext("REASON")

        return Modification(change=change, reason=reason)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
