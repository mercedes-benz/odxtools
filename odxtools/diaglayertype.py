# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from enum import Enum


class DiagLayerType(Enum):
    PROTOCOL = "PROTOCOL"
    FUNCTIONAL_GROUP = "FUNCTIONAL-GROUP"
    BASE_VARIANT = "BASE-VARIANT"
    ECU_VARIANT = "ECU-VARIANT"
    ECU_SHARED_DATA = "ECU-SHARED-DATA"

    @classmethod
    def from_str(cls, value: str):
        if value not in cls._value2member_map_.keys():
            raise ValueError(
                f"{value} is not a string representation of a DiagLayerType enum instance.")
        return cls._value2member_map_[value]
