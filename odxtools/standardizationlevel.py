# SPDX-License-Identifier: MIT
from enum import StrEnum


class StandardizationLevel(StrEnum):
    STANDARD = "STANDARD"
    OEM_SPECIFIC = "OEM-SPECIFIC"
    OPTIONAL = "OPTIONAL"
    OEM_OPTIONAL = "OEM-OPTIONAL"
