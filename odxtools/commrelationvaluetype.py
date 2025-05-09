# SPDX-License-Identifier: MIT
from enum import StrEnum


class CommRelationValueType(StrEnum):
    CURRENT = "CURRENT"
    STORED = "STORED"
    STATIC = "STATIC"
    SUBSTITUTED = "SUBSTITUTED"
