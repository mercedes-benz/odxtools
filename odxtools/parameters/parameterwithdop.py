# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from ..dataobjectproperty import DataObjectProperty
from ..decodestate import DecodeState
from ..dopbase import DopBase
from ..dtcdop import DtcDop
from ..encodestate import EncodeState
from ..exceptions import odxassert, odxrequire
from ..odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..physicaltype import PhysicalType
from .parameter import Parameter

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class ParameterWithDOP(Parameter):
    dop_ref: Optional[OdxLinkRef]
    dop_snref: Optional[str]

    def __post_init__(self) -> None:
        odxassert(self.dop_snref is not None or self.dop_ref is not None,
                  f"Param {self.short_name} without a DOP-(SN)REF should not exist!")

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.dop_ref is not None:
            odxassert(self.dop_snref is None)
            # TODO: do not do lenient resolves here. The problem is
            # that currently not all kinds of DOPs are internalized
            # (e.g., static and dynamic fields)
            self._dop = odxlinks.resolve_lenient(self.dop_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        if self.dop_snref:
            spec = diag_layer.diag_data_dictionary_spec
            self._dop = (
                spec.data_object_props.get(self.dop_snref) or spec.structures.get(self.dop_snref))

    @property
    def dop(self) -> Optional[DopBase]:
        """may be a DataObjectProperty, a Structure or None"""

        return self._dop

    @property
    def bit_length(self):
        if self.dop is not None:
            return self.dop.bit_length
        else:
            return None

    @property
    def physical_type(self) -> Optional[PhysicalType]:
        if isinstance(self.dop, (DataObjectProperty, DtcDop)):
            return self.dop.physical_type
        else:
            return None

    def get_coded_value(self, physical_value=None):
        return self.dop.convert_physical_to_internal(physical_value)

    def get_coded_value_as_bytes(self, encode_state: EncodeState):
        dop = odxrequire(self.dop, "Reference to DOP is not resolved")
        physical_value = encode_state.parameter_values[self.short_name]
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return dop.convert_physical_to_bytes(
            physical_value, encode_state, bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[Any, int]:
        dop = odxrequire(self.dop, "Reference to DOP is not resolved")
        decode_state = copy(decode_state)
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            decode_state.next_byte_position = self.byte_position

        # Use DOP to decode
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        phys_val, next_byte_position = dop.convert_bytes_to_physical(
            decode_state, bit_position=bit_position_int)

        return phys_val, next_byte_position

    def _as_dict(self):
        d = super()._as_dict()
        if self.dop is not None:
            if self.bit_length is not None:
                d["bit_length"] = self.bit_length
            d["dop_ref"] = OdxLinkRef.from_id(self.dop.odx_id)
        elif self.dop_ref is not None:
            d["dop_ref"] = self.dop_ref
        elif self.dop_snref is not None:
            d["dop_snref"] = self.dop_snref

        return d
