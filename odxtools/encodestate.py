# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .tablerow import TableRow


@dataclass
class EncodeState:
    """Utility class to holding the state variables needed for encoding a message.
    """

    #: payload that is constructed so far
    coded_message: bytes

    #: a mapping from short name to value for each parameter
    parameter_values: Dict[str, Any]

    #: If encoding a response: request that triggered the response
    triggering_request: Optional[bytes] = None

    #: Mapping from the short name of a length-key parameter to bit
    #: lengths (specified by LengthKeyParameter)
    length_keys: Dict[str, int] = field(default_factory=dict)

    #: Mapping from the short name of a table-key parameter to the
    #: corresponding row of the table (specified by TableKeyParameter)
    table_keys: Dict[str, "TableRow"] = field(default_factory=dict)

    #: Flag whether we are currently the last parameter of the PDU
    #: (needed for MinMaxLengthType)
    is_end_of_pdu: bool = False
