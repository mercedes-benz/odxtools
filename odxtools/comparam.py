# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .dataobjectproperty import DataObjectProperty
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class Comparam(BaseComparam):
    dop_ref: OdxLinkRef
    physical_default_value: str

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Comparam":
        kwargs = dataclass_fields_asdict(BaseComparam.from_et(et_element, doc_frags))

        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags))
        physical_default_value = odxrequire(et_element.findtext("PHYSICAL-DEFAULT-VALUE"))

        return Comparam(dop_ref=dop_ref, physical_default_value=physical_default_value, **kwargs)

    @property
    def dop(self) -> DataObjectProperty:
        """The data object property describing this parameter."""
        return self._dop

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Resolves the reference to the dop"""
        super()._resolve_odxlinks(odxlinks)

        self._dop = odxlinks.resolve(self.dop_ref, DataObjectProperty)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)
