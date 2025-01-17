# SPDX-License-Identifier: MIT
from enum import Enum


class Encoding(Enum):
    BCD_P = "BCD-P"
    BCD_UP = "BCD-UP"

    ONEC = "1C"
    TWOC = "2C"
    SM = "SM"

    UTF8 = "UTF-8"
    UCS2 = "UCS-2"
    ISO_8859_1 = "ISO-8859-1"
    ISO_8859_2 = "ISO-8859-2"
    WINDOWS_1252 = "WINDOWS-1252"

    NONE = "NONE"
