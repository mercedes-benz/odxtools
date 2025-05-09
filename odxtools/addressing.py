# SPDX-License-Identifier: MIT
from enum import StrEnum


class Addressing(StrEnum):
    FUNCTIONAL = "FUNCTIONAL"
    PHYSICAL = "PHYSICAL"
    FUNCTIONAL_OR_PHYSICAL = "FUNCTIONAL-OR-PHYSICAL"
