# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .globals import xsi
from .matchingcomponent import MatchingComponent
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


class InfoComponentType(Enum):
    EcuProxy = "ECU-PROXY"
    ModelYear = "MODEL-YEAR"
    Oem = "OEM"
    VehicleModel = "VEHICLE-MODEL"
    VehicleType = "VEHICLE-TYPE"


@dataclass(kw_only=True)
class InfoComponent(IdentifiableElement):
    component_type: InfoComponentType
    matching_components: list[MatchingComponent]

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "InfoComponent":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        component_type_str = odxrequire(et_element.attrib.get(f"{xsi}type"))
        try:
            component_type = InfoComponentType(component_type_str)
        except ValueError:
            odxraise(f"Encountered unknown INFO-COMPONENT type '{component_type_str}'")
            component_type = cast(InfoComponentType, None)

        matching_components = [
            MatchingComponent.from_et(mc_elem, context)
            for mc_elem in et_element.iterfind("MATCHING-COMPONENTS/MATCHING-COMPONENT")
        ]

        return InfoComponent(
            component_type=component_type, matching_components=matching_components, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for matching_component in self.matching_components:
            result.update(matching_component._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for matching_component in self.matching_components:
            matching_component._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for matching_component in self.matching_components:
            matching_component._resolve_snrefs(context)
