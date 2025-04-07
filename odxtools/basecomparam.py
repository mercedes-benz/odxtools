# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .standardizationlevel import StandardizationLevel
from .usage import Usage
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class BaseComparam(IdentifiableElement):
    param_class: str
    cptype: StandardizationLevel
    display_level: int | None = None
    cpusage: Usage | None = None  # Required in ODX 2.2, missing in ODX 2.0

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "BaseComparam":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        param_class = odxrequire(et_element.attrib.get("PARAM-CLASS"))

        cptype_str = odxrequire(et_element.attrib.get("CPTYPE"))
        try:
            cptype = StandardizationLevel(cptype_str)
        except ValueError:
            cptype = cast(StandardizationLevel, None)
            odxraise(f"Encountered unknown CPTYPE '{cptype_str}'")

        dl = et_element.attrib.get("DISPLAY_LEVEL")
        display_level = None if dl is None else int(dl)

        # Required in ODX 2.2, missing in ODX 2.0
        cpusage_str = et_element.attrib.get("CPUSAGE")
        cpusage = None
        if cpusage_str is not None:
            try:
                cpusage = Usage(cpusage_str)
            except ValueError:
                cpusage = None
                odxraise(f"Encountered unknown CPUSAGE '{cpusage_str}'")

        return BaseComparam(
            param_class=param_class,
            cptype=cptype,
            display_level=display_level,
            cpusage=cpusage,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
