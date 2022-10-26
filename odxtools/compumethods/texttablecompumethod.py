# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import List

from ..exceptions import DecodeError
from ..odxtypes import DataType

from .compumethodbase import CompuMethod
from .compuscale import CompuScale


class TexttableCompuMethod(CompuMethod):
    def __init__(self, internal_to_phys: List[CompuScale], internal_type):
        super().__init__(internal_type, DataType.A_UNICODE2STRING, "TEXTTABLE")
        self.internal_to_phys = internal_to_phys

        assert all(scale.lower_limit is not None or scale.upper_limit is not None
                   for scale in self.internal_to_phys), "Text table compu method doesn't have expected format!"

    def convert_physical_to_internal(self, physical_value):
        scale = next(filter(
            lambda scale: scale.compu_const == physical_value, self.internal_to_phys), None)
        if scale is not None:
            res = scale.compu_inverse_value if scale.compu_inverse_value is not None else scale.lower_limit.value
            assert self.internal_type.isinstance(res)
            return res

    def __is_internal_in_scale(self, internal_value, scale: CompuScale):
        if scale.lower_limit is not None and not scale.lower_limit.complies_to_lower(internal_value):
            return False
        if scale.upper_limit is not None and not scale.upper_limit.complies_to_upper(internal_value):
            return False
        # value complies to the defined limits
        return True

    def convert_internal_to_physical(self, internal_value):
        try:
            scale = next(filter(lambda scale: self.__is_internal_in_scale(internal_value, scale),
                                self.internal_to_phys))
        except StopIteration:
            raise DecodeError(
                f"Texttable compu method could not decode {internal_value} to string.")
        return scale.compu_const

    def is_valid_physical_value(self, physical_value):
        return physical_value in [ x.compu_const for x in self.internal_to_phys ]

    def is_valid_internal_value(self, internal_value):
        return any(self.__is_internal_in_scale(internal_value, scale) for scale in self.internal_to_phys)

    def get_valid_physical_values(self):
        return [ x.compu_const for x in self.internal_to_phys ]
