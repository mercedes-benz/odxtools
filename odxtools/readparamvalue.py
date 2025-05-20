# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class ReadParamValue:
    phys_constant_value: str

    # exactly one of the following attributes must be non-None
    in_param_if_snref: str | None = None
    in_param_if_snpathref: str | None = None

    semantic: str

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ReadParamValue":
        phys_constant_value = odxrequire(et_element.findtext("PHYS-CONSTANT-VALUE"))

        in_param_if_snref = None
        if (in_param_if_snref_elem := et_element.find("IN-PARAM-IF-SNREF")) is not None:
            in_param_if_snref = odxrequire(in_param_if_snref_elem.attrib.get("SHORT-NAME"))

        in_param_if_snpathref = None
        if (in_param_if_snpathref_elem := et_element.find("IN-PARAM-IF-SNPATHREF")) is not None:
            in_param_if_snpathref = odxrequire(
                in_param_if_snpathref_elem.attrib.get("SHORT-NAME-PATH"))

        semantic = odxrequire(et_element.attrib.get("SEMANTIC"))

        return ReadParamValue(
            phys_constant_value=phys_constant_value,
            in_param_if_snref=in_param_if_snref,
            in_param_if_snpathref=in_param_if_snpathref,
            semantic=semantic,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}
        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
