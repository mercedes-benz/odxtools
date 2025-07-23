# SPDX-License-Identifier: MIT
from enum import Enum


class DataformatSelection(Enum):
    INTEL_HEX = "INTEL-HEX"
    MOTOROLA_S = "MOTOROLA-S"
    BINARY = "BINARY"
    USER_DEFINED = "USER-DEFINED"
