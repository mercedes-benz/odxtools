# SPDX-License-Identifier: MIT
from enum import Enum


class ValidType(Enum):
    VALID = "VALID"
    NOT_VALID = "NOT-VALID"
    NOT_DEFINED = "NOT-DEFINED"
    NOT_AVAILABLE = "NOT-AVAILABLE"
