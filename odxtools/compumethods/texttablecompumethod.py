# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional

from ..exceptions import DecodeError, EncodeError, odxassert
from ..odxtypes import DataType
from .compumethod import CompuMethod, CompuMethodCategory
from .compuscale import CompuScale


@dataclass
class TexttableCompuMethod(CompuMethod):

    internal_to_phys: List[CompuScale]
    # For compu_default_value, the compu_const is always defined
    # the compu_inverse_value is optional
    compu_default_value: Optional[CompuScale]

    def __post_init__(self) -> None:
        odxassert(self.physical_type == DataType.A_UNICODE2STRING,
                  "TEXTTABLE must have A_UNICODE2STRING as its physical datatype.")
        odxassert(
            all(scale.lower_limit is not None or scale.upper_limit is not None
                for scale in self.internal_to_phys),
            "Text table compu method doesn't have expected format!")

    @property
    def category(self) -> CompuMethodCategory:
        return "TEXTTABLE"

    def _get_scales(self):
        scales = list(self.internal_to_phys)
        if self.compu_default_value:
            # Default is last, since it's a fallback
            scales.append(self.compu_default_value)
        return scales

    def convert_physical_to_internal(self, physical_value):
        scale: CompuScale = next(
            filter(lambda scale: scale.compu_const == physical_value, self._get_scales()), None)
        if scale is not None:
            res = (
                scale.compu_inverse_value
                if scale.compu_inverse_value is not None else scale.lower_limit.value)
            odxassert(self.internal_type.isinstance(res))
            return res
        raise EncodeError(f"Texttable compu method could not encode '{physical_value}'.")

    def __is_internal_in_scale(self, internal_value, scale: CompuScale):
        if scale == self.compu_default_value:
            return True
        if scale.lower_limit is not None and not scale.lower_limit.complies_to_lower(
                internal_value):
            return False
        # If no UPPER-LIMIT is defined
        # the COMPU-SCALE will be applied only for the value defined in LOWER-LIMIT
        upper_limit = scale.upper_limit or scale.lower_limit
        if upper_limit is not None and not upper_limit.complies_to_upper(internal_value):
            return False
        # value complies to the defined limits
        return True

    def convert_internal_to_physical(self, internal_value):
        scale = next(
            filter(
                lambda scale: self.__is_internal_in_scale(internal_value, scale),
                self._get_scales(),
            ), None)
        if scale is None:
            raise DecodeError(
                f"Texttable compu method could not decode {internal_value} to string.")
        return scale.compu_const

    def is_valid_physical_value(self, physical_value):
        return physical_value in self.get_valid_physical_values()

    def is_valid_internal_value(self, internal_value):
        return any(
            self.__is_internal_in_scale(internal_value, scale) for scale in self._get_scales())

    def get_valid_physical_values(self):
        return [x.compu_const for x in self._get_scales()]
