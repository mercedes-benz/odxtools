# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .odxtypes import ParameterValueDict


@dataclass
class DecodeState:
    """Utility class to be used while decoding a message."""

    #: bytes to be decoded
    coded_message: bytes

    #: values of already decoded parameters
    parameter_values: ParameterValueDict

    #: Position of the next parameter if its position is not specified in ODX
    cursor_position: int
