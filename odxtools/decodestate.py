# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Any, Dict, List, NamedTuple, Union


class ParameterValuePair(NamedTuple):
    parameter: Any  # This should be a Parameter but that would lead to a cyclic import
    value: Union[str, int, bytes, bytearray, Dict]


class DecodeState(NamedTuple):
    """Utility class to be used while decoding a message."""
    # bytes to be decoded
    coded_message: Union[bytes, bytearray]
    # values of already decoded parameters
    parameter_value_pairs: List[ParameterValuePair]
    # Position of the next parameter if its position is not specified in ODX
    next_byte_position: int
