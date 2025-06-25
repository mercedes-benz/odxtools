# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .audience import Audience
from .configitem import ConfigItem
from .itemvalue import ItemValue
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class OptionItem(ConfigItem):
    """This class represents a OPTION-ITEM."""

    physical_default_value: str | None = None
    item_values: list[ItemValue] = field(default_factory=list)
    write_audience: Audience | None = None
    read_audience: Audience | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "OptionItem":
        kwargs = dataclass_fields_asdict(ConfigItem.from_et(et_element, context))

        physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")

        item_values = [
            ItemValue.from_et(el, context) for el in et_element.iterfind("ITEM-VALUES/ITEM-VALUE")
        ]

        write_audience = None
        if (wa_elem := et_element.find("WRITE-AUDIENCE")) is not None:
            write_audience = Audience.from_et(wa_elem, context)

        read_audience = None
        if (ra_elem := et_element.find("READ-AUDIENCE")) is not None:
            read_audience = Audience.from_et(ra_elem, context)

        return OptionItem(
            physical_default_value=physical_default_value,
            item_values=item_values,
            write_audience=write_audience,
            read_audience=read_audience,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for item_value in self.item_values:
            result.update(item_value._build_odxlinks())
        if self.write_audience is not None:
            result.update(self.write_audience._build_odxlinks())
        if self.read_audience is not None:
            result.update(self.read_audience._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for item_value in self.item_values:
            item_value._resolve_odxlinks(odxlinks)
        if self.write_audience is not None:
            self.write_audience._resolve_odxlinks(odxlinks)
        if self.read_audience is not None:
            self.read_audience._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for item_value in self.item_values:
            item_value._resolve_snrefs(context)
        if self.write_audience is not None:
            self.write_audience._resolve_snrefs(context)
        if self.read_audience is not None:
            self.read_audience._resolve_snrefs(context)
