# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import Iterable

from ..globals import logger

from .compumethodbase import CompuMethod
from .linearcompumethod import LinearCompuMethod


class ScaleLinearCompuMethod(CompuMethod):
    def __init__(self, linear_methods: Iterable[LinearCompuMethod]):
        super().__init__(list(linear_methods)[0].internal_type,
                         list(linear_methods)[0].physical_type,
                         "SCALE-LINEAR")
        self.linear_methods = list(linear_methods)
        logger.debug("Created scale linear compu method!")

    def convert_physical_to_internal(self, physical_value):
        assert self.is_valid_physical_value(physical_value), \
            f"cannot convert the invalid physical value {physical_value} of type {type(physical_value)}"
        lin_method = next(
            scale for scale in self.linear_methods if scale.is_valid_physical_value(physical_value))
        return lin_method.convert_physical_to_internal(physical_value)

    def convert_internal_to_physical(self, internal_value):
        lin_method = next(
            scale for scale in self.linear_methods if scale.is_valid_internal_value(internal_value))
        return lin_method.convert_internal_to_physical(internal_value)

    def is_valid_physical_value(self, physical_value):
        return any(True for scale in self.linear_methods if scale.is_valid_physical_value(physical_value))

    def is_valid_internal_value(self, internal_value):
        return any(True for scale in self.linear_methods if scale.is_valid_internal_value(internal_value))
