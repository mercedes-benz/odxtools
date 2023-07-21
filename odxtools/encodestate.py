# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from typing import Any, Dict, NamedTuple, Optional, Union

from .odxlink import OdxLinkId
from .odxtypes import AtomicOdxType


@dataclass
class EncodeState:
    """Utility class to be used while encoding a message.

    While encoding parameters may update the dicts with new keys
    but this is the only allowed change.
    In particular the coded_message is not updated in-place.
    Instead the new encode state can be constructed with::

        for p in self.parameters:
            prefix = p.encode_into_pdu(encode_state)
            encode_state = encode_state._replace(coded_message=prefix)

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

    #: Flag whether the parameter is the last on the PDU (needed for MinMaxLengthType)
    is_end_of_pdu: bool = False
