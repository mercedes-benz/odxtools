# SPDX-License-Identifier: MIT
from typing import Optional

from .basicstructure import BasicStructure


class Response(BasicStructure):

    def __init__(self, *, response_type: str, **kwargs):  # "POS-RESPONSE" or "NEG-RESPONSE"
        super().__init__(**kwargs)

        self.response_type = response_type

    def encode(self, coded_request: Optional[bytes] = None, **params) -> bytes:
        if coded_request is not None:
            # Extract MATCHING-REQUEST-PARAMs from the coded request
            for param in self.parameters:
                if param.parameter_type == "MATCHING-REQUEST-PARAM":
                    byte_pos = param.request_byte_position
                    byte_length = param.byte_length

                    val = coded_request[byte_pos:byte_pos + byte_length]
                    params[param.short_name] = val

        return super().encode(coded_request=coded_request, **params)

    def __repr__(self) -> str:
        return f"Response('{self.short_name}')"

    def __str__(self) -> str:
        return f"Response('{self.short_name}')"
