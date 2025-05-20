# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .audience import Audience
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .text import Text


@dataclass(kw_only=True)
class ItemValue:
    """This class represents a ITEM-VALUE."""

    phys_constant_value: str | None
    meaning: Text | None = None
    key: str | None = None
    rule: str | None = None
    description: Text | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    audience: Audience | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ItemValue":
        phys_constant_value = et_element.findtext("PHYS-CONSTANT-VALUE")

        meaning = None
        if (meaning_elem := et_element.find("MEANING")) is not None:
            meaning = Text.from_et(meaning_elem, context)

        key = et_element.findtext("KEY")
        rule = et_element.findtext("RULE")

        description = None
        if (description_elem := et_element.find("DESCRIPTION")) is not None:
            description = Text.from_et(description_elem, context)

        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        audience = None
        if (aud_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(aud_elem, context)

        return ItemValue(
            phys_constant_value=phys_constant_value,
            meaning=meaning,
            key=key,
            rule=rule,
            description=description,
            sdgs=sdgs,
            audience=audience,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        if self.audience is not None:
            result.update(self.audience._build_odxlinks())
        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.audience is not None:
            self.audience._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.audience is not None:
            self.audience._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
