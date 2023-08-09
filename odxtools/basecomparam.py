# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .utils import create_description_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


class StandardizationLevel(Enum):
    STANDARD = "STANDARD"
    OEM_SPECIFIC = "OEM-SPECIFIC"
    OPTIONAL = "OPTIONAL"
    OEM_OPTIONAL = "OEM-OPTIONAL"


class Usage(Enum):
    ECU_SOFTWARE = "ECU-SOFTWARE"
    ECU_COMM = "ECU-COMM"
    APPLICATION = "APPLICATION"
    TESTER = "TESTER"


@dataclass
class BaseComparam:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    param_class: str
    cptype: StandardizationLevel
    cpusage: Usage
    display_level: Optional[int]

    def __init_from_et__(self, et_element: ElementTree.Element,
                         doc_frags: List[OdxDocFragment]) -> None:
        self.odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        self.short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        self.long_name = et_element.findtext("LONG-NAME")
        self.description = create_description_from_et(et_element.find("DESC"))
        self.param_class = odxrequire(et_element.attrib.get("PARAM-CLASS"))

        cptype_str = odxrequire(et_element.attrib.get("CPTYPE"))
        try:
            self.cptype = StandardizationLevel(cptype_str)
        except ValueError:
            self.cptype = cast(StandardizationLevel, None)
            odxraise(f"Encountered unknown CPTYPE '{cptype_str}'")

        cpusage_str = odxrequire(et_element.attrib.get("CPUSAGE"))
        try:
            self.cpusage = Usage(cpusage_str)
        except ValueError:
            self.cpusage = cast(Usage, None)
            odxraise(f"Encountered unknown CPUSAGE '{cpusage_str}'")

        dl = et_element.attrib.get("DISPLAY_LEVEL")
        self.display_level = None if dl is None else int(dl)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
