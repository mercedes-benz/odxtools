# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Any, Dict, NamedTuple, Optional, Union


class EncodeState(NamedTuple):
    """Utility class to be used while encoding a message.

    While encoding parameters may update the dicts with new keys 
    but this is the only allowed change.
    In particular the coded_message is not updated in-place.
    Instead the new encode state can be constructed with:
    ```
    for p in self.parameters:
        prefix = p.encode_into_pdu(encode_state)
        encode_state = encode_state._replace(coded_message=prefix)
    ``` 
    """
    # payload that is constructed so far
    coded_message: bytes
    # a mapping from short name to value for each parameter
    parameter_values: Dict[str, Any]
    # For encoding a response: request that triggered the response
    triggering_request: Optional[Union[bytes, bytearray]] = None
    # Mapping from IDs to bit lengths (specified by LengthKeyParameters)
    length_keys: Dict[str, int] = {}
    # Flag whether the parameter is the last on the PDU (needed for MinMaxLengthType)
    is_end_of_pdu: bool = False
