# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Union

from .odxtypes import ParameterValueDict

if TYPE_CHECKING:
    from .parameters.parameterbase import Parameter
    from .tablerow import TableRow


@dataclass
class DecodeState:
    """Utility class to be used while decoding a message."""

    #: bytes to be decoded
    coded_message: bytes

    #: values of already decoded parameters
    parameter_values: ParameterValueDict

    #: Position of the next parameter if its position is not specified in ODX
    next_byte_position: int
