# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .dataobjectproperty import DataObjectProperty
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .unitspec import UnitSpec


@dataclass(kw_only=True)
class ConfigDataDictionarySpec:
    data_object_props: NamedItemList[DataObjectProperty] = field(default_factory=NamedItemList)
    unit_spec: UnitSpec | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "ConfigDataDictionarySpec":
        data_object_props = NamedItemList([
            DataObjectProperty.from_et(dop_element, context)
            for dop_element in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ])

        if (spec_elem := et_element.find("UNIT-SPEC")) is not None:
            unit_spec = UnitSpec.from_et(spec_elem, context)
        else:
            unit_spec = None

        return ConfigDataDictionarySpec(
            data_object_props=data_object_props,
            unit_spec=unit_spec,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {}

        for data_object_prop in self.data_object_props:
            odxlinks.update(data_object_prop._build_odxlinks())
        if self.unit_spec is not None:
            odxlinks.update(self.unit_spec._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for data_object_prop in self.data_object_props:
            data_object_prop._resolve_odxlinks(odxlinks)
        if self.unit_spec is not None:
            self.unit_spec._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for data_object_prop in self.data_object_props:
            data_object_prop._resolve_snrefs(context)
        if self.unit_spec is not None:
            self.unit_spec._resolve_snrefs(context)
