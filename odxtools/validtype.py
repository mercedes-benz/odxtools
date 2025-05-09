# SPDX-License-Identifier: MIT
from enum import StrEnum


class ValidType(StrEnum):
    VALID = "VALID"
    NOT_VALID = "NOT-VALID"
    NOT_DEFINED = "NOT-DEFINED"
    NOT_AVAILABLE = "NOT-AVAILABLE"
