# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Union

from ..odxtypes import DataType
from .compumethod import CompuMethod, CompuMethodCategory


@dataclass
class IdenticalCompuMethod(CompuMethod):

    @property
    def category(self) -> CompuMethodCategory:
        return "IDENTICAL"

    def convert_physical_to_internal(self, physical_value):
        return physical_value

    def convert_internal_to_physical(self, internal_value):
        return internal_value

    def is_valid_physical_value(self, physical_value):
        return self.physical_type.isinstance(physical_value)

    def is_valid_internal_value(self, internal_value):
        return self.internal_type.isinstance(internal_value)
