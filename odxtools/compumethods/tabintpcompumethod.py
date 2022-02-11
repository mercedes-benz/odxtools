# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from ..globals import logger

from .compumethodbase import CompuMethod


class TabIntpCompuMethod(CompuMethod):
    def __init__(self,
                 internal_type,
                 physical_type):
        super().__init__(internal_type, physical_type, "TAB-INTP")
        logger.debug("Created table interpolation compu method!")
        logger.warning(
            "TODO: Implement table interpolation compu method properly!")

    def convert_physical_to_internal(self, physical_value):
        return self.internal_type.cast(physical_value)

    def convert_internal_to_physical(self, internal_value):
        return self.physical_type.cast(internal_value)

    def is_valid_physical_value(self, physical_value):
        return True

    def is_valid_internal_value(self, internal_value):
        return True
