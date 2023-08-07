# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Audience:
    enabled_audience_refs: List[OdxLinkRef]
    disabled_audience_refs: List[OdxLinkRef]

    is_supplier_raw: Optional[bool]

    @property
    def is_supplier(self) -> bool:
        return self.is_supplier_raw in [None, True]

    is_development_raw: Optional[bool]

    @property
    def is_development(self) -> bool:
        return self.is_development_raw in [None, True]

    is_manufacturing_raw: Optional[bool]

    @property
    def is_manufacturing(self) -> bool:
        return self.is_manufacturing_raw in [None, True]

    is_aftersales_raw: Optional[bool]

    @property
    def is_aftersales(self) -> bool:
        return self.is_aftersales_raw in [None, True]

    is_aftermarket_raw: Optional[bool]

    @property
    def is_aftermarket(self) -> bool:
        return self.is_aftermarket_raw in [None, True]

    @property
    def enabled_audiences(self) -> List[AdditionalAudience]:
        return self._enabled_audiences

    @property
    def disabled_audiences(self) -> List[AdditionalAudience]:
        return self._disabled_audiences

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Audience":

        enabled_audience_refs = [
            OdxLinkRef.from_et(ref, doc_frags)
            for ref in et_element.iterfind("ENABLED-AUDIENCE-REFS/"
                                           "ENABLED-AUDIENCE-REF")
        ]
        disabled_audience_refs = [
            OdxLinkRef.from_et(ref, doc_frags)
            for ref in et_element.iterfind("DISABLED-AUDIENCE-REFS/"
                                           "DISABLED-AUDIENCE-REF")
        ]
        is_supplier_raw = odxstr_to_bool(et_element.get("IS-SUPPLIER"))
        is_development_raw = odxstr_to_bool(et_element.get("IS-DEVELOPMENT"))
        is_manufacturing_raw = odxstr_to_bool(et_element.get("IS-MANUFACTURING"))
        is_aftersales_raw = odxstr_to_bool(et_element.get("IS-AFTERSALES"))
        is_aftermarket_raw = odxstr_to_bool(et_element.get("IS-AFTERMARKET"))

        return Audience(
            enabled_audience_refs=enabled_audience_refs,
            disabled_audience_refs=disabled_audience_refs,
            is_supplier_raw=is_supplier_raw,
            is_development_raw=is_development_raw,
            is_manufacturing_raw=is_manufacturing_raw,
            is_aftersales_raw=is_aftersales_raw,
            is_aftermarket_raw=is_aftermarket_raw,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._enabled_audiences = [
            odxlinks.resolve(ref, AdditionalAudience) for ref in self.enabled_audience_refs
        ]
        self._disabled_audiences = [
            odxlinks.resolve(ref, AdditionalAudience) for ref in self.disabled_audience_refs
        ]

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
