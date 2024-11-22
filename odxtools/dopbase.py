# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .admindata import AdminData
from .decodestate import DecodeState
from .element import IdentifiableElement
from .encodestate import EncodeState
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass
class DopBase(IdentifiableElement):
    """Base class for all (simple and complex) data object properties.

    Any class that a parameter can reference via a DOP-REF (Simple
    DOPs, structures, ...) inherits from this class. All DOPs objects
    implement the `Codec` type protocol.

    """

    admin_data: Optional[AdminData]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DopBase":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = None
        if (admin_data_elem := et_element.find("ADMIN-DATA")) is not None:
            admin_data = AdminData.from_et(admin_data_elem, doc_frags)

        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        return DopBase(admin_data=admin_data, sdgs=sdgs, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

    def get_static_bit_length(self) -> Optional[int]:
        return None

    def is_valid_physical_value(self, physical_value: ParameterValue) -> bool:
        """Determine if a phyical value can be handled by the DOP"""
        raise NotImplementedError

    def encode_into_pdu(self, physical_value: ParameterValue, encode_state: EncodeState) -> None:
        """Convert the physical value to bytes and emplace them into a PDU."""
        raise NotImplementedError

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        """Extract the bytes from the PDU and convert them to the physical value."""
        raise NotImplementedError
