# SPDX-License-Identifier: MIT
from enum import Enum


class CompuCategory(Enum):
    IDENTICAL = "IDENTICAL"
    LINEAR = "LINEAR"
    SCALE_LINEAR = "SCALE-LINEAR"
    TEXTTABLE = "TEXTTABLE"
    COMPUCODE = "COMPUCODE"
    TAB_INTP = "TAB-INTP"
    RAT_FUNC = "RAT-FUNC"
    SCALE_RAT_FUNC = "SCALE-RAT-FUNC"
