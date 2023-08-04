# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree.ElementTree import Element

from .exceptions import odxrequire
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

    def __init_from_et__(self, et_element: Element, doc_frags: List[OdxDocFragment]) -> None:
        self.odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        self.short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        self.long_name = et_element.findtext("LONG-NAME")
        self.description = create_description_from_et(et_element.find("DESC"))
        self.param_class = odxrequire(et_element.attrib.get("PARAM-CLASS"))
        self.cptype = StandardizationLevel(odxrequire(et_element.attrib.get("CPTYPE")))
        self.cpusage = Usage(odxrequire(et_element.attrib.get("CPUSAGE")))
        dl = et_element.attrib.get("DISPLAY_LEVEL")
        self.display_level = None if dl is None else int(dl)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
