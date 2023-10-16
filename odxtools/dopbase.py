# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .decodestate import DecodeState
from .element import IdentifiableElement
from .encodestate import EncodeState
from .odxlink import OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .specialdatagroup import SpecialDataGroup

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DopBase(IdentifiableElement):
    """Base class for all DOPs.

    Any class that a parameter can reference via a DOP-REF should inherit from this class.
    """

    is_visible_raw: Optional[bool]
    sdgs: List[SpecialDataGroup]

    def __hash__(self) -> int:
        result = 0

        result += hash(self.short_name)
        result += hash(self.long_name)
        result += hash(self.description)
        result += hash(self.is_visible_raw)

        return result

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

    def get_static_bit_length(self) -> Optional[int]:
        return None

    def is_valid_physical_value(self, physical_value: ParameterValue) -> bool:
        """Determine if a phyical value can be handled by the DOP
        """
        raise NotImplementedError

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw in (None, True)

    def convert_physical_to_bytes(self, physical_value: ParameterValue, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        """Convert the physical value into bytes."""
        raise NotImplementedError

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValue, int]:
        """Extract the bytes from the PDU and convert them to the physical value."""
        raise NotImplementedError
