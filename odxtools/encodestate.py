# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Any, Dict, NamedTuple, Optional, Union

from .odxlink import OdxLinkId

class EncodeState(NamedTuple):
    """Utility class to be used while encoding a message.

    While encoding parameters may update the dicts with new keys 
    but this is the only allowed change.
    In particular the coded_message is not updated in-place.
    Instead the new encode state can be constructed with::

        for p in self.parameters:
            prefix = p.encode_into_pdu(encode_state)
            encode_state = encode_state._replace(coded_message=prefix)

    """
    coded_message: bytes
    """payload that is constructed so far"""
    parameter_values: Dict[str, Any]
    """a mapping from short name to value for each parameter"""
    triggering_request: Optional[Union[bytes, bytearray]] = None
    """If encoding a response: request that triggered the response"""
    length_keys: Dict[OdxLinkId, int] = {}
    """Mapping from IDs to bit lengths (specified by LengthKeyParameters)"""
    is_end_of_pdu: bool = False
    """Flag whether the parameter is the last on the PDU (needed for MinMaxLengthType)"""
