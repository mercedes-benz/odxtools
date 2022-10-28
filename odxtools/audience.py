# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass, field
from typing import Optional, List
from odxtools.utils import read_description_from_odx
from .odxlink import OdxLinkRef, OdxLinkId, OdxDocFragment, OdxLinkDatabase

@dataclass()
class Audience:
    enabled_audience_refs: list = field(default_factory=list)
    disabled_audience_refs: list = field(default_factory=list)
    is_supplier: bool = True
    is_development: bool = True
    is_manufacturing: bool = True
    is_aftersales: bool = True
    is_aftermarket: bool = True

    _enabled_audiences: Optional[List["Audience"]] = None
    _disabled_audiences: Optional[List["Audience"]] = None

    @property
    def enabled_audiences(self):
        return self._enabled_audiences

    @property
    def disabled_audiences(self):
        return self._disabled_audiences

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


def read_audience_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    enabled_audience_refs = [OdxLinkRef.from_et(ref, doc_frags)
        for ref in et_element.iterfind("ENABLED-AUDIENCE-REFS/"
                                       "ENABLED-AUDIENCE-REF")]
    disabled_audience_refs = [OdxLinkRef.from_et(ref, doc_frags)
        for ref in et_element.iterfind("DISABLED-AUDIENCE-REFS/"
                                       "DISABLED-AUDIENCE-REF")]
    is_supplier = et_element.get("IS-SUPPLIER", "true") == 'true'
    is_development = et_element.get("IS-DEVELOPMENT", "true") == 'true'
    is_manufacturing = et_element.get("IS-MANUFACTURING", "true") == 'true'
    is_aftersales = et_element.get("IS-AFTERSALES", "true") == 'true'
    is_aftermarket = et_element.get("IS-AFTERMARKET", "true") == 'true'

    return Audience(enabled_audience_refs=enabled_audience_refs,
                    disabled_audience_refs=disabled_audience_refs,
                    is_supplier=is_supplier,
                    is_development=is_development,
                    is_manufacturing=is_manufacturing,
                    is_aftersales=is_aftersales,
                    is_aftermarket=is_aftermarket)


def read_additional_audience_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    short_name = et_element.find("SHORT-NAME").text
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None

    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    return AdditionalAudience(odx_id=odx_id,
                              short_name=short_name,
                              long_name=long_name,
                              description=description)
