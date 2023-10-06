from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .dataobjectproperty import DataObjectProperty
from .exceptions import odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class DetermineNumberOfItems:
    """
    The object that determines the number of items of dynamic fields
    """
    byte_position: int
    bit_position: Optional[int]
    dop_ref: OdxLinkRef

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DetermineNumberOfItems":
        byte_position = int(odxrequire(et_element.findtext("BYTE-POSITION")))
        bit_position_str = et_element.findtext("BIT-POSITION")
        bit_position = int(bit_position_str) if bit_position_str is not None else None
        dop_ref = odxrequire(OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags))

        return DetermineNumberOfItems(
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_ref, DataObjectProperty)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop(self) -> DataObjectProperty:
        return self._dop
