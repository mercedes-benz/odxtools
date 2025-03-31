# SPDX-License-Identifier: MIT
from enum import Enum


class Addressing(Enum):
    FUNCTIONAL = "FUNCTIONAL"
    PHYSICAL = "PHYSICAL"
    FUNCTIONAL_OR_PHYSICAL = "FUNCTIONAL-OR-PHYSICAL"
