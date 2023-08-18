# SPDX-License-Identifier: MIT
import abc
from dataclasses import dataclass
from typing import Literal, Union

from ..odxtypes import DataType

CompuMethodCategory = Literal[
    "IDENTICAL",
    "LINEAR",
    "SCALE-LINEAR",
    "TAB-INTP",
    "TEXTTABLE",
]


@dataclass
class CompuMethod(abc.ABC):
    internal_type: DataType
    physical_type: DataType

    @property
    @abc.abstractmethod
    def category(self) -> CompuMethodCategory:
        pass

    def convert_physical_to_internal(self, physical_value):
        raise NotImplementedError()

    def convert_internal_to_physical(self, internal_value) -> Union[int, float, str]:
        raise NotImplementedError()

    def is_valid_physical_value(self, physical_value):
        raise NotImplementedError()

    def is_valid_internal_value(self, internal_value):
        raise NotImplementedError()

    def get_valid_physical_values(self):
        return None
