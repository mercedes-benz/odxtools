# SPDX-License-Identifier: MIT
from enum import Enum

from .odxtypes import DataType


class IdentValueType(Enum):
    A_UINT32 = "A_UINT32"
    A_BYTEFIELD = "A_BYTEFIELD"
    A_ASCIISTRING = "A_ASCIISTRING"

    @property
    def data_type(self) -> DataType:
        return DataType(self.value)
