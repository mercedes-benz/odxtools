# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .tablerow import TableRow


@dataclass
class DecodeState:
    """Utility class to be used while decoding a message."""

    #: bytes to be decoded
    coded_message: bytes

    #: Absolute position of the origin
    #:
    #: i.e., the absolute byte position to which all relative positions
    #: refer to, e.g. the position of the first byte of a structure.
    origin_byte_position: int = 0

    #: Absolute position of the next undecoded byte to be considered
    #:
    #: (if not explicitly specified by the object to be decoded.)
    cursor_byte_position: int = 0

    #: the bit position [0, 7] where the object to be extracted begins
    #:
    #: If bit position is undefined (`None`), the object to be extracted
    #: starts at bit 0.
    cursor_bit_position: Optional[int] = None

    #: values of the length key parameters decoded so far
    length_keys: Dict[str, int] = field(default_factory=dict)

    #: values of the table key parameters decoded so far
    table_keys: Dict[str, "TableRow"] = field(default_factory=dict)
