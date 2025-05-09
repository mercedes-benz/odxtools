# SPDX-License-Identifier: MIT
from enum import Enum


class Termination(Enum):
    END_OF_PDU = "END-OF-PDU"
    ZERO = "ZERO"
    HEX_FF = "HEX-FF"
