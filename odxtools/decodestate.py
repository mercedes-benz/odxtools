# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Any, Dict, List, NamedTuple, Union


class ParameterValuePair(NamedTuple):
    parameter: Any  # This should be a Parameter but that would lead to a cyclic import
    value: Union[str, int, bytes, bytearray, Dict]


class DecodeState(NamedTuple):
    """Utility class to be used while decoding a message."""
    coded_message: Union[bytes, bytearray]
    """bytes to be decoded"""
    parameter_value_pairs: List[ParameterValuePair]
    """values of already decoded parameters"""
    next_byte_position: int
    """Position of the next parameter if its position is not specified in ODX"""
