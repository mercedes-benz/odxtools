# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .dopbase import DopBase
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .utils import create_description_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class InputParam:
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str]
    description: Optional[str]
    oid: Optional[str]
    semantic: Optional[str]
    physical_default_value: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "InputParam":
        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        dop_base_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags))
        physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")

        semantic = et_element.get("SEMANTIC")
        oid = et_element.get("OID")

        return InputParam(
            short_name=short_name,
            long_name=long_name,
            description=description,
            dop_base_ref=dop_base_ref,
            physical_default_value=physical_default_value,
            semantic=semantic,
            oid=oid,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref, DopBase)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop(self) -> DopBase:
        """The data object property describing this parameter."""
        return self._dop
