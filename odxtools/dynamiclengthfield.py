# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Tuple
from xml.etree import ElementTree

from .decodestate import DecodeState
from .determinenumberofitems import DetermineNumberOfItems
from .encodestate import EncodeState
from .exceptions import odxrequire
from .field import Field
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DynamicLengthField(Field):
    """Array of structure with length field"""
    offset: int
    determine_number_of_items: DetermineNumberOfItems

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DynamicLengthField":
        kwargs = dataclass_fields_asdict(Field.from_et(et_element, doc_frags))
        offset = int(odxrequire(et_element.findtext('OFFSET')))
        determine_number_of_items = DetermineNumberOfItems.from_et(
            odxrequire(et_element.find('DETERMINE-NUMBER-OF-ITEMS')),
            doc_frags,
        )
        return DynamicLengthField(
            offset=offset, determine_number_of_items=determine_number_of_items, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        odxlinks.update(self.determine_number_of_items._build_odxlinks())
        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)
        self.determine_number_of_items._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)
        self.determine_number_of_items._resolve_snrefs(diag_layer)

    def convert_physical_to_bytes(
        self,
        physical_value: ParameterValue,
        encode_state: EncodeState,
        bit_position: int = 0,
    ) -> bytes:
        raise NotImplementedError()

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValue, int]:
        raise NotImplementedError()
