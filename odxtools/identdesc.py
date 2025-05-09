# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class IdentDesc:
    diag_comm_snref: str
    ident_if_snref: str

    # exactly one of the two attributes below must be defined
    out_param_if_snref: str | None = None
    out_param_if_snpathref: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "IdentDesc":
        diag_comm_snref = odxrequire(
            odxrequire(et_element.find("DIAG-COMM-SNREF")).attrib.get("SHORT-NAME"))
        ident_if_snref = odxrequire(
            odxrequire(et_element.find("IDENT-IF-SNREF")).attrib.get("SHORT-NAME"))
        out_param_if_snref = None
        if (out_param_if_snref_elem := et_element.find("OUT-PARAM-IF-SNREF")) is not None:
            out_param_if_snref = odxrequire(out_param_if_snref_elem.attrib.get("SHORT-NAME"))

        out_param_if_snpathref = None
        if (out_param_if_snpathref_elem := et_element.find("OUT-PARAM-IF-SNPATHREF")) is not None:
            out_param_if_snpathref = odxrequire(
                out_param_if_snpathref_elem.attrib.get("SHORT-NAME-PATH"))

        return IdentDesc(
            diag_comm_snref=diag_comm_snref,
            ident_if_snref=ident_if_snref,
            out_param_if_snref=out_param_if_snref,
            out_param_if_snpathref=out_param_if_snpathref,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # TODO: resolve the short name references. for IdentDesc this
        # is (probably) not possible ahead of time...
        pass
