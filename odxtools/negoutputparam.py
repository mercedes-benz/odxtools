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
class NegOutputParam:
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str]
    description: Optional[str]

    def __post_init__(self) -> None:
        self._dop: Optional[DopBase] = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "NegOutputParam":

        short_name = odxrequire(et_element.findtext("SHORT-NAME"))
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        dop_base_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags))

        return NegOutputParam(
            short_name=short_name,
            long_name=long_name,
            description=description,
            dop_base_ref=dop_base_ref,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop(self) -> Optional[DopBase]:
        """The data object property describing this parameter."""
        return self._dop
