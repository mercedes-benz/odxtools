# SPDX-License-Identifier: MIT
from enum import Enum


class PinType(Enum):
    HI = "HI"
    LOW = "LOW"
    K = "K"
    L = "L"
    TX = "TX"
    RX = "RX"
    PLUS = "PLUS"
    MINUS = "MINUS"
    SINGLE = "SINGLE"
