# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import Optional, Union

from ..dataobjectproperty import DataObjectProperty, DopBase, DtcDop
from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..physicaltype import PhysicalType
from ..globals import logger
from ..odxlink import OdxLinkRef, OdxLinkDatabase

from .parameterbase import Parameter


class ParameterWithDOP(Parameter):
    def __init__(self,
                 short_name: str,
                 parameter_type: str,
                 dop=None,
                 dop_ref: Optional[OdxLinkRef] = None,
                 dop_snref: Optional[str] = None,
                 **kwargs):
        super().__init__(short_name, parameter_type, **kwargs)
        self.dop_ref = dop_ref
        self.dop_snref = dop_snref

        self._dop = dop
        if dop and not dop_ref and not dop_snref:
            self.dop_ref = OdxLinkRef.from_id(dop.odx_id)
        assert self.dop_ref or self.dop_snref

    @property
    def dop(self) -> Union[DopBase, None]:
        """may be a DataObjectProperty, a Structure or None"""
        return self._dop

    @dop.setter
    def dop(self, dop: DopBase):
        self._dop = dop
        if not self.dop_snref:
            self.dop_ref = OdxLinkRef.from_id(dop.odx_id)
        else:
            self.dop_snref = dop.short_name

    def resolve_references(self, parent_dl, odxlinks: OdxLinkDatabase):
        dop = self.dop
        if self.dop_snref:
            dop = parent_dl.data_object_properties.get(self.dop_snref)
            if dop is None:
                logger.info(
                    f"Param {self.short_name} could not resolve DOP-SNREF {self.dop_snref}")
        elif self.dop_ref:
            dop = odxlinks.resolve_lenient(self.dop_ref) # TODO: non-lenient!
            if dop is None:
                logger.info(
                    f"Param {self.short_name} could not resolve DOP-REF {self.dop_ref}")
        else:
            logger.warn(
                f"Param {self.short_name} without DOP-(SN)REF should not exist!")
        if self.dop and dop != self.dop:
            logger.warn(
                f"Param {self.short_name}: Reference and DOP are inconsistent!")

        self._dop = dop

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
        return self.dop.convert_physical_to_bytes(physical_value,
                                                  encode_state,
                                                  bit_position=bit_position_int)

    def decode_from_pdu(self, decode_state: DecodeState):
        assert self.dop is not None, "Reference to DOP is not resolved"
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            decode_state = decode_state._replace(
                next_byte_position=self.byte_position)

        # Use DOP to decode
        bit_position_int = self.bit_position if self.bit_position is not None else 0
        phys_val, next_byte_position = \
            self.dop.convert_bytes_to_physical(decode_state,
                                               bit_position=bit_position_int)

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
        lines = [
            super().__str__(),
            " " + str(self.dop).replace("\n", "\n ")
        ]
        return "\n".join(lines)
