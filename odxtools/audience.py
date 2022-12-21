# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .utils import create_description_from_et, str_to_bool
from .odxlink import OdxLinkRef, OdxLinkId, OdxDocFragment, OdxLinkDatabase

@dataclass()
class Audience:
    enabled_audience_refs: list = field(default_factory=list)
    disabled_audience_refs: list = field(default_factory=list)

    _is_supplier: Optional[bool] = None
    @property
    def is_supplier(self) -> bool:
        return self._is_supplier in [None, True]

    _is_development: Optional[bool] = None
    @property
    def is_development(self) -> bool:
        return self._is_development in [None, True]

    _is_manufacturing: Optional[bool] = None
    @property
    def is_manufacturing(self) -> bool:
        return self._is_manufacturing in [None, True]

    _is_aftersales: Optional[bool] = None
    @property
    def is_aftersales(self) -> bool:
        return self._is_aftersales in [None, True]

    _is_aftermarket: Optional[bool] = None
    @property
    def is_aftermarket(self) -> bool:
        return self._is_aftermarket in [None, True]

    _enabled_audiences: Optional[List["AdditionalAudience"]] = None
    @property
    def enabled_audiences(self) -> List["AdditionalAudience"]:
        assert self._enabled_audiences is not None
        return self._enabled_audiences

    _disabled_audiences: Optional[List["AdditionalAudience"]] = None
    @property
    def disabled_audiences(self) -> List["AdditionalAudience"]:
        assert self._disabled_audiences is not None
        return self._disabled_audiences

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "Audience":

        enabled_audience_refs = [OdxLinkRef.from_et(ref, doc_frags)
            for ref in et_element.iterfind("ENABLED-AUDIENCE-REFS/"
                                           "ENABLED-AUDIENCE-REF")]
        disabled_audience_refs = [OdxLinkRef.from_et(ref, doc_frags)
            for ref in et_element.iterfind("DISABLED-AUDIENCE-REFS/"
                                           "DISABLED-AUDIENCE-REF")]
        is_supplier = str_to_bool(et_element.get("IS-SUPPLIER"))
        is_development = str_to_bool(et_element.get("IS-DEVELOPMENT"))
        is_manufacturing = str_to_bool(et_element.get("IS-MANUFACTURING"))
        is_aftersales = str_to_bool(et_element.get("IS-AFTERSALES"))
        is_aftermarket = str_to_bool(et_element.get("IS-AFTERMARKET"))

        return Audience(enabled_audience_refs=enabled_audience_refs,
                        disabled_audience_refs=disabled_audience_refs,
                        _is_supplier=is_supplier,
                        _is_development=is_development,
                        _is_manufacturing=is_manufacturing,
                        _is_aftersales=is_aftersales,
                        _is_aftermarket=is_aftermarket)


    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self._enabled_audiences = [odxlinks.resolve(ref)
                                   for ref in self.enabled_audience_refs]
        self._disabled_audiences = [odxlinks.resolve(ref)
                                    for ref in self.disabled_audience_refs]


@dataclass()
class AdditionalAudience:
    """
    Corresponds to ADDITIONAL-AUDIENCE.
    """
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "AdditionalAudience":

        short_name = et_element.findtext("SHORT-NAME")
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None

        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        return AdditionalAudience(odx_id=odx_id,
                                  short_name=short_name,
                                  long_name=long_name,
                                  description=description)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return { self.odx_id: self }

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        pass
