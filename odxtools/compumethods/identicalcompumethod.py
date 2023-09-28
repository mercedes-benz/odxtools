# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from ..odxtypes import AtomicOdxType
from .compumethod import CompuMethod, CompuMethodCategory


@dataclass
class IdenticalCompuMethod(CompuMethod):

    @property
    def category(self) -> CompuMethodCategory:
        return "IDENTICAL"

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        return physical_value

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        return internal_value

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return self.physical_type.isinstance(physical_value)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return self.internal_type.isinstance(internal_value)
