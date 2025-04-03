# SPDX-License-Identifier: MIT
from enum import Enum


class StandardizationLevel(Enum):
    STANDARD = "STANDARD"
    OEM_SPECIFIC = "OEM-SPECIFIC"
    OPTIONAL = "OPTIONAL"
    OEM_OPTIONAL = "OEM-OPTIONAL"
