# SPDX-License-Identifier: MIT
from enum import StrEnum


class Termination(StrEnum):
    END_OF_PDU = "END-OF-PDU"
    ZERO = "ZERO"
    HEX_FF = "HEX-FF"
