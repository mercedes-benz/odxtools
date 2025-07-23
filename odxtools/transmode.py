# SPDX-License-Identifier: MIT
from enum import Enum


class TransMode(Enum):
    SEND_ONLY = "SEND-ONLY"
    RECEIVE_ONLY = "RECEIVE-ONLY"
    SEND_AND_RECEIVE = "SEND-AND-RECEIVE"
    SEND_OR_RECEIVE = "SEND-OR-RECEIVE"
