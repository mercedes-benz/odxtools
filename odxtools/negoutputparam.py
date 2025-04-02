# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .dopbase import DopBase
from .element import NamedElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class NegOutputParam(NamedElement):
    dop_base_ref: OdxLinkRef

    @property
    def dop(self) -> DopBase:
        """The data object property describing this parameter."""
        return self._dop

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: list[OdxDocFragment]) -> "NegOutputParam":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))
        dop_base_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags))

        return NegOutputParam(dop_base_ref=dop_base_ref, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref, DopBase)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
