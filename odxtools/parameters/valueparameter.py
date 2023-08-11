# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..dataobjectproperty import DataObjectProperty
from ..encodestate import EncodeState
from ..exceptions import odxraise, odxrequire
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class ValueParameter(ParameterWithDOP):
    physical_default_value_raw: Optional[str]

    @property
    def parameter_type(self) -> ParameterType:
        return "VALUE"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        self._physical_default_value: Optional[AtomicOdxType]
        pdvr = self.physical_default_value_raw
        if pdvr is None:
            self._physical_default_value = None
            return

        dop = odxrequire(self.dop)
        if not isinstance(dop, DataObjectProperty):
            odxraise("The type of PHYS-CONST parameters must be a simple DOP")
        base_data_type = dop.physical_type.base_data_type
        self._physical_default_value = base_data_type.from_string(pdvr)

    @property
    def physical_default_value(self) -> Optional[AtomicOdxType]:
        return self._physical_default_value

    def is_required(self) -> bool:
        return self.physical_default_value is None

    def is_optional(self) -> bool:
        return not self.is_required()

    def get_coded_value(self, physical_value: Optional[AtomicOdxType] = None):
        if physical_value is not None:
            dop = odxrequire(self.dop)
            if not isinstance(dop, DataObjectProperty):
                odxraise()
            return dop.convert_physical_to_internal(physical_value)
        else:
            return self.physical_default_value

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        physical_value = encode_state.parameter_values.get(self.short_name,
                                                           self.physical_default_value)
        if physical_value is None:
            raise TypeError(f"A value for parameter '{self.short_name}' must be specified"
                            f" as the parameter does not exhibit a default.")
        dop = odxrequire(
            self.dop,
            f"Param {self.short_name} does not have a DOP. Maybe resolving references failed?")

        bit_position_int = self.bit_position if self.bit_position is not None else 0
        return dop.convert_physical_to_bytes(
            physical_value, encode_state=encode_state, bit_position=bit_position_int)

    def get_valid_physical_values(self):
        if isinstance(self.dop, DataObjectProperty):
            return self.dop.get_valid_physical_values()
