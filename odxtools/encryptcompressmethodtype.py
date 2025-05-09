# SPDX-License-Identifier: MIT
from enum import StrEnum

from .odxtypes import DataType


class EncryptCompressMethodType(StrEnum):
    A_UINT32 = "A_UINT32"
    A_BYTEFIELD = "A_BYTEFIELD"

    @property
    def data_type(self) -> DataType:
        return DataType(self.value)
