# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class Audience:
    enabled_audience_refs: list[OdxLinkRef] = field(default_factory=list)
    disabled_audience_refs: list[OdxLinkRef] = field(default_factory=list)

    is_supplier_raw: bool | None = None
    is_development_raw: bool | None = None
    is_manufacturing_raw: bool | None = None
    is_aftersales_raw: bool | None = None
    is_aftermarket_raw: bool | None = None

    @property
    def is_supplier(self) -> bool:
        return self.is_supplier_raw in [None, True]

    @property
    def is_development(self) -> bool:
        return self.is_development_raw in [None, True]

    @property
    def is_manufacturing(self) -> bool:
        return self.is_manufacturing_raw in [None, True]

    @property
    def is_aftersales(self) -> bool:
        return self.is_aftersales_raw in [None, True]

    @property
    def is_aftermarket(self) -> bool:
        return self.is_aftermarket_raw in [None, True]

    @property
    def enabled_audiences(self) -> NamedItemList[AdditionalAudience]:
        return self._enabled_audiences

    @property
    def disabled_audiences(self) -> NamedItemList[AdditionalAudience]:
        return self._disabled_audiences

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Audience":

        enabled_audience_refs = [
            OdxLinkRef.from_et(ref, context) for ref in et_element.iterfind("ENABLED-AUDIENCE-REFS/"
                                                                            "ENABLED-AUDIENCE-REF")
        ]
        disabled_audience_refs = [
            OdxLinkRef.from_et(ref, context)
            for ref in et_element.iterfind("DISABLED-AUDIENCE-REFS/"
                                           "DISABLED-AUDIENCE-REF")
        ]
        is_supplier_raw = odxstr_to_bool(et_element.attrib.get("IS-SUPPLIER"))
        is_development_raw = odxstr_to_bool(et_element.attrib.get("IS-DEVELOPMENT"))
        is_manufacturing_raw = odxstr_to_bool(et_element.attrib.get("IS-MANUFACTURING"))
        is_aftersales_raw = odxstr_to_bool(et_element.attrib.get("IS-AFTERSALES"))
        is_aftermarket_raw = odxstr_to_bool(et_element.attrib.get("IS-AFTERMARKET"))

        return Audience(
            enabled_audience_refs=enabled_audience_refs,
            disabled_audience_refs=disabled_audience_refs,
            is_supplier_raw=is_supplier_raw,
            is_development_raw=is_development_raw,
            is_manufacturing_raw=is_manufacturing_raw,
            is_aftersales_raw=is_aftersales_raw,
            is_aftermarket_raw=is_aftermarket_raw,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._enabled_audiences = NamedItemList(
            [odxlinks.resolve(ref, AdditionalAudience) for ref in self.enabled_audience_refs])
        self._disabled_audiences = NamedItemList(
            [odxlinks.resolve(ref, AdditionalAudience) for ref in self.disabled_audience_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
