# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .comparamsubset import ComparamSubset
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ProtStack(IdentifiableElement):
    # mandatory in ODX 2.2, but non existent in ODX 2.0
    pdu_protocol_type: str
    physical_link_type: str
    comparam_subset_refs: list[OdxLinkRef] = field(default_factory=list)

    @property
    def comparam_subsets(self) -> NamedItemList[ComparamSubset]:
        return self._comparam_subsets

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ProtStack":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        pdu_protocol_type = odxrequire(et_element.findtext("PDU-PROTOCOL-TYPE"))
        physical_link_type = odxrequire(et_element.findtext("PHYSICAL-LINK-TYPE"))
        comparam_subset_refs = [
            OdxLinkRef.from_et(csr_element, context)
            for csr_element in et_element.iterfind("COMPARAM-SUBSET-REFS/"
                                                   "COMPARAM-SUBSET-REF")
        ]

        return ProtStack(
            pdu_protocol_type=pdu_protocol_type,
            physical_link_type=physical_link_type,
            comparam_subset_refs=comparam_subset_refs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}
        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._comparam_subsets = NamedItemList[ComparamSubset](
            [odxlinks.resolve(x, ComparamSubset) for x in self.comparam_subset_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
