# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional

from .basicstructure import BasicStructure
from .odxtypes import ParameterValue
from .parameters.matchingrequestparameter import MatchingRequestParameter


@dataclass
class Response(BasicStructure):
    response_type: str  # "POS-RESPONSE" or "NEG-RESPONSE"

    def encode(self, coded_request: Optional[bytes] = None, **params: ParameterValue) -> bytes:
        if coded_request is not None:
            # Extract MATCHING-REQUEST-PARAMs from the coded
            # request. TODO: this should be done by
            # MatchingRequestParam itself!
            for param in self.parameters:
                if isinstance(param, MatchingRequestParameter):
                    byte_pos = param.request_byte_position
                    byte_length = param.byte_length

                    val = coded_request[byte_pos:byte_pos + byte_length]
                    params[param.short_name] = val

        return super().encode(coded_request=coded_request, **params)
