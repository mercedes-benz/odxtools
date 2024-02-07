# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict

from .odxtypes import ParameterValueDict

if TYPE_CHECKING:
    from .tablerow import TableRow


@dataclass
class DecodeState:
    """Utility class to be used while decoding a message."""

    #: bytes to be decoded
    coded_message: bytes

    # TODO: remove this!
    parameter_values: ParameterValueDict

    #: Absolute position of the origin
    #:
    #: i.e., the absolute byte position to which all relative positions
    #: refer to, e.g. the position of the first byte of a structure.
    origin_position: int = 0

    #: Absolute position of the next undecoded byte to be considered
    #:
    #: (if not explicitly specified by the object to be decoded.)
    cursor_position: int = 0

    #: values of the length key parameters decoded so far
    length_keys: Dict[str, int] = field(default_factory=dict)

    #: values of the table key parameters decoded so far
    table_keys: Dict[str, "TableRow"] = field(default_factory=dict)
