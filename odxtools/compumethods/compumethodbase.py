# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


import abc
from typing import Union

from ..odxtypes import DataType


class CompuMethod:

    def __init__(self,
                 internal_type: Union[DataType, str],
                 physical_type: Union[DataType, str],
                 category: str):
        self.internal_type = DataType(internal_type)
        self.physical_type = DataType(physical_type)
        self.category = category

    def convert_physical_to_internal(self, physical_value):
        raise NotImplementedError()

    def convert_internal_to_physical(self, internal_value) \
        -> Union[int, float, str]:
        raise NotImplementedError()

    def is_valid_physical_value(self, physical_value):
        raise NotImplementedError()

    def is_valid_internal_value(self, internal_value):
        raise NotImplementedError()

    def get_valid_physical_values(self):
        return None
