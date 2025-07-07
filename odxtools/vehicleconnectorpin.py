# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .pintype import PinType
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class VehicleConnectorPin(IdentifiableElement):
    pin_number: int

    pin_type: PinType

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "VehicleConnectorPin":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        pin_number = int(odxrequire(et_element.findtext("PIN-NUMBER")) or "0")

        pin_type_str = odxrequire(et_element.attrib.get("TYPE"))
        try:
            pin_type = PinType(pin_type_str)
        except ValueError:
            odxraise(f"Encountered unknown PIN type '{pin_type_str}'")
            pin_type = cast(PinType, None)

        return VehicleConnectorPin(pin_number=pin_number, pin_type=pin_type, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
