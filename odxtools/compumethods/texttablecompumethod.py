# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional

from ..exceptions import DecodeError, EncodeError, odxassert
from ..odxtypes import AtomicOdxType, DataType
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

    def get_scales(self) -> List[CompuScale]:
        scales = list(self.internal_to_phys)
        if self.compu_default_value:
            # Default is last, since it's a fallback
            scales.append(self.compu_default_value)
        return scales

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        matching_scales = [x for x in self.get_scales() if x.compu_const == physical_value]
        for scale in matching_scales:
            if scale.compu_inverse_value is not None:
                return scale.compu_inverse_value
            elif scale.lower_limit is not None:
                return scale.lower_limit.value
            elif scale.upper_limit is not None:
                return scale.upper_limit.value

        raise EncodeError(f"Texttable compu method could not encode '{physical_value!r}'.")

    def __is_internal_in_scale(self, internal_value: AtomicOdxType, scale: CompuScale) -> bool:
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

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        scale = next(
            filter(
                lambda scale: self.__is_internal_in_scale(internal_value, scale),
                self.get_scales(),
            ), None)
        if scale is None or scale.compu_const is None:
            raise DecodeError(
                f"Texttable compu method could not decode {internal_value!r} to string.")
        return scale.compu_const

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return any(x.compu_const == physical_value for x in self.get_scales())

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return any(
            self.__is_internal_in_scale(internal_value, scale) for scale in self.get_scales())
