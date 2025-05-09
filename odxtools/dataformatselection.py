# SPDX-License-Identifier: MIT
from enum import StrEnum


class DataformatSelection(StrEnum):
    INTEL_HEX = "INTEL-HEX"
    MOTOROLA_S = "MOTOROLA-S"
    BINARY = "BINARY"
    USER_DEFINED = "USER-DEFINED"
