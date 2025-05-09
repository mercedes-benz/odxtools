# SPDX-License-Identifier: MIT
from enum import StrEnum


class Usage(StrEnum):
    ECU_SOFTWARE = "ECU-SOFTWARE"
    ECU_COMM = "ECU-COMM"
    APPLICATION = "APPLICATION"
    TESTER = "TESTER"
