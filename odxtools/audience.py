# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass, field
from typing import Optional
from odxtools.utils import read_description_from_odx


@dataclass()
class Audience:
    enabled_audience_refs: list = field(default_factory=list)
    disabled_audience_refs: list = field(default_factory=list)
    is_supplier: bool = True
    is_development: bool = True
    is_manufacturing: bool = True
    is_aftersales: bool = True
    is_aftermarket: bool = True

    @property
    def enabled_audiences(self):
        return self._enabled_audiences

    @property
    def disabled_audiences(self):
        return self._disabled_audiences

    def _resolve_references(self, id_lookup):
        self._enabled_audiences = [id_lookup[ref]
                                   for ref in self.enabled_audience_refs]
        self._disabled_audiences = [id_lookup[ref]
                                    for ref in self.disabled_audience_refs]


@dataclass()
class AdditionalAudience:
    """
    Corresponds to ADDITIONAL-AUDIENCE.
    """
    id: str
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None


def read_audience_from_odx(et_element):
    enabled_audience_refs = [ref.get(
        "ID-REF") for ref in et_element.iterfind("ENABLED-AUDIENCE-REFS/ENABLED-AUDIENCE-REF")]
    disabled_audience_refs = [ref.get(
        "ID-REF") for ref in et_element.iterfind("DISABLED-AUDIENCE-REFS/DISABLED-AUDIENCE-REF")]
    is_supplier = et_element.get(
        "IS-SUPPLIER") == 'true' if et_element.get("IS-SUPPLIER") else True
    is_development = et_element.get(
        "IS-DEVELOPMENT") == 'true' if et_element.get("IS-DEVELOPMENT") else True
    is_manufacturing = et_element.get(
        "IS-MANUFACTURING") == 'true' if et_element.get("IS-MANUFACTURING") else True
    is_aftersales = et_element.get(
        "IS-AFTERSALES") == 'true' if et_element.get("IS-AFTERSALES") else True
    is_aftermarket = et_element.get(
        "IS-AFTERMARKET") == 'true' if et_element.get("IS-AFTERMARKET") else True

    return Audience(enabled_audience_refs=enabled_audience_refs,
                    disabled_audience_refs=disabled_audience_refs,
                    is_supplier=is_supplier,
                    is_development=is_development,
                    is_manufacturing=is_manufacturing,
                    is_aftersales=is_aftersales,
                    is_aftermarket=is_aftermarket)


def read_additional_audience_from_odx(et_element):
    short_name = et_element.find("SHORT-NAME").text
    id = et_element.get("ID")

    long_name = et_element.find(
        "LONG-NAME").text if et_element.find("LONG-NAME") is not None else None
    description = read_description_from_odx(et_element.find("DESC"))

    return AdditionalAudience(id=id,
                              short_name=short_name,
                              long_name=long_name,
                              description=description)
