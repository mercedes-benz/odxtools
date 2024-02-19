# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional

from .exceptions import OdxWarning

if TYPE_CHECKING:
    from .tablerow import TableRow


@dataclass
class EncodeState:
    """Utility class to holding the state variables needed for encoding a message.
    """

    #: payload that has been constructed so far
    coded_message: bytearray

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

    def emplace_atomic_value(self,
                             new_data: bytes,
                             param_name: str,
                             pos: Optional[int] = None) -> None:
        if pos is None:
            pos = len(self.coded_message)

        # Make blob longer if necessary
        min_length = pos + len(new_data)
        if len(self.coded_message) < min_length:
            self.coded_message.extend([0] * (min_length - len(self.coded_message)))

        for byte_idx_val, byte_idx_rpc in enumerate(range(pos, pos + len(new_data))):
            # insert byte value
            if self.coded_message[byte_idx_rpc] & new_data[byte_idx_val] != 0:
                warnings.warn(
                    f"Object '{param_name}' overlaps with another parameter (bytes are already set)",
                    OdxWarning,
                    stacklevel=1,
                )
            self.coded_message[byte_idx_rpc] |= new_data[byte_idx_val]
