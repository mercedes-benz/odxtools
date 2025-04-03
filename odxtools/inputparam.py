# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from deprecation import deprecated

from .dopbase import DopBase
from .element import NamedElement
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class InputParam(NamedElement):
    physical_default_value: str | None
    dop_base_ref: OdxLinkRef
    oid: str | None
    semantic: str | None

    @property
    def dop(self) -> DopBase:
        """The data object property describing this parameter."""
        return self._dop

    @deprecated(details="use .dop")  # type: ignore[misc]
    def dop_base(self) -> DopBase:
        return self._dop

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: list[OdxDocFragment]) -> "InputParam":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))

        physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")
        dop_base_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags))

        oid = et_element.get("OID")
        semantic = et_element.get("SEMANTIC")

        return InputParam(
            physical_default_value=physical_default_value,
            dop_base_ref=dop_base_ref,
            oid=oid,
            semantic=semantic,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref, DopBase)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
