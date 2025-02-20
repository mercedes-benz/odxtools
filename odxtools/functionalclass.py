# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .admindata import AdminData
from .element import IdentifiableElement
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class FunctionalClass(IdentifiableElement):
    """
    Corresponds to FUNCT-CLASS.
    """

    admin_data: Optional[AdminData]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "FunctionalClass":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)

        return FunctionalClass(admin_data=admin_data, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
