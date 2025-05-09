# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from .dataformatselection import DataformatSelection
from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class Dataformat:
    selection: DataformatSelection
    user_selection: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Dataformat":
        selection_str = odxrequire(et_element.attrib.get("SELECTION"))
        try:
            selection = DataformatSelection(selection_str)
        except ValueError:
            selection = cast(DataformatSelection, None)
            odxraise(f"Encountered unknown data format selection '{selection_str}'")
        user_selection = et_element.attrib.get("USER-SELECTION")

        return Dataformat(selection=selection, user_selection=user_selection)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
