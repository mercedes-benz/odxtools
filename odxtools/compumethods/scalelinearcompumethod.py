# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List

from ..exceptions import odxassert
from ..odxtypes import AtomicOdxType
from .compumethod import CompuMethod, CompuMethodCategory
from .linearcompumethod import LinearCompuMethod


@dataclass
class ScaleLinearCompuMethod(CompuMethod):
    linear_methods: List[LinearCompuMethod]

    @property
    def category(self) -> CompuMethodCategory:
        return "SCALE-LINEAR"

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        odxassert(
            self.is_valid_physical_value(physical_value),
            f"cannot convert the invalid physical value {physical_value!r} "
            f"of type {type(physical_value)}")
        lin_method = next(
            scale for scale in self.linear_methods if scale.is_valid_physical_value(physical_value))
        return lin_method.convert_physical_to_internal(physical_value)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        lin_method = next(
            scale for scale in self.linear_methods if scale.is_valid_internal_value(internal_value))
        return lin_method.convert_internal_to_physical(internal_value)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return any(
            True for scale in self.linear_methods if scale.is_valid_physical_value(physical_value))

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return any(
            True for scale in self.linear_methods if scale.is_valid_internal_value(internal_value))
