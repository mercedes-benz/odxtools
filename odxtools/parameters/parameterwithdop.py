# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from copy import copy
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from ..dataobjectproperty import DataObjectProperty, DopBase, DtcDop
from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..globals import logger
from ..odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..physicaltype import PhysicalType
from .parameterbase import Parameter

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


class ParameterWithDOP(Parameter):

    def __init__(
        self,
        *,
        parameter_type: str,
        dop_ref: Optional[OdxLinkRef],
        dop_snref: Optional[str],
        **kwargs,
    ) -> None:
        super().__init__(parameter_type=parameter_type, **kwargs)
        self.dop_ref = dop_ref
        self.dop_snref = dop_snref

        self._dop: Optional[DopBase] = None
        if dop_snref is None and dop_ref is None:
            logger.warn(f"Param {self.short_name} without DOP-(SN)REF should not exist!")

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.dop_ref is not None:
            assert self.dop_snref is None
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
        assert self.dop is not None, "Reference to DOP is not resolved"
        physical_value = encode_state.parameter_values[self.short_name]
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return self.dop.convert_physical_to_bytes(
            physical_value, encode_state, bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[Any, int]:
        assert self.dop is not None, "Reference to DOP is not resolved"
        decode_state = copy(decode_state)
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            decode_state.next_byte_position = self.byte_position

        # Use DOP to decode
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        phys_val, next_byte_position = self.dop.convert_bytes_to_physical(
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

    def __str__(self):
        lines = [super().__str__(), " " + str(self.dop).replace("\n", "\n ")]
        return "\n".join(lines)
