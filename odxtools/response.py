# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, cast
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .exceptions import odxraise
from .odxlink import OdxDocFragment
from .odxtypes import ParameterValue
from .parameters.matchingrequestparameter import MatchingRequestParameter
from .utils import dataclass_fields_asdict


class ResponseType(Enum):
    POSITIVE = "POS-RESPONSE"
    NEGATIVE = "NEG-RESPONSE"
    GLOBAL_NEGATIVE = "GLOBAL-NEG-RESPONSE"


# TODO: The spec does not say that responses are basic structures. For
# now, we derive from it anyway because it simplifies the en- and
# decoding machinery...
@dataclass
class Response(BasicStructure):
    response_type: ResponseType

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Response":
        """Reads a response."""
        kwargs = dataclass_fields_asdict(BasicStructure.from_et(et_element, doc_frags))

        try:
            response_type = ResponseType(et_element.tag)
        except ValueError:
            response_type = cast(ResponseType, None)
            odxraise(f"Encountered unknown response type '{et_element.tag}'")

        return Response(response_type=response_type, **kwargs)

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
