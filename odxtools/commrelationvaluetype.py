# SPDX-License-Identifier: MIT
from enum import Enum


class CommRelationValueType(Enum):
    CURRENT = "CURRENT"
    STORED = "STORED"
    STATIC = "STATIC"
    SUBSTITUTED = "SUBSTITUTED"
