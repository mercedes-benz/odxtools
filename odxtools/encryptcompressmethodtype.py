# SPDX-License-Identifier: MIT
from enum import Enum

from .odxtypes import DataType


class EncryptCompressMethodType(Enum):
    A_UINT32 = "A_UINT32"
    A_BYTEFIELD = "A_BYTEFIELD"

    @property
    def data_type(self) -> DataType:
        return DataType(self.value)
