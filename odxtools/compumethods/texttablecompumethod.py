# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional, cast

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
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

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        matching_scales = [x for x in self.internal_to_phys if x.compu_const == physical_value]
        for scale in matching_scales:
            if scale.compu_inverse_value is not None:
                return scale.compu_inverse_value
            elif scale.lower_limit is not None and scale.lower_limit._value is not None:
                return scale.lower_limit._value
            elif scale.upper_limit is not None and scale.upper_limit._value is not None:
                return scale.upper_limit._value

        if self.compu_default_value is not None and self.compu_default_value.compu_inverse_value is not None:
            return self.compu_default_value.compu_inverse_value

        raise EncodeError(f"Texttable compu method could not encode '{physical_value!r}'.")

    def __is_internal_in_scale(self, internal_value: AtomicOdxType, scale: CompuScale) -> bool:
        if scale == self.compu_default_value:
            return True

        return scale.applies(internal_value)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        matching_scales = [x for x in self.internal_to_phys if x.applies(internal_value)]
        if len(matching_scales) == 0:
            if self.compu_default_value is None or self.compu_default_value.compu_const is None:
                odxraise(f"Texttable could not decode {internal_value!r}.", DecodeError)
                return cast(None, AtomicOdxType)

            return self.compu_default_value.compu_const

        if len(matching_scales) != 1 or matching_scales[0].compu_const is None:
            odxraise(f"Texttable could not decode {internal_value!r}.", DecodeError)

        return matching_scales[0].compu_const

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        if self.compu_default_value is not None:
            return True

        return any(x.compu_const == physical_value for x in self.internal_to_phys)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        if self.compu_default_value is not None:
            return True

        return any(scale.applies(internal_value) for scale in self.internal_to_phys)
