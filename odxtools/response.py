# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, cast
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .encodestate import EncodeState
from .exceptions import odxraise
from .odxlink import OdxDocFragment
from .odxtypes import ParameterValue
from .snrefcontext import SnRefContext
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

    def encode(self, coded_request: Optional[bytes] = None, **kwargs: ParameterValue) -> bytes:
        encode_state = EncodeState(triggering_request=coded_request, is_end_of_pdu=True)

        self.encode_into_pdu(physical_value=kwargs, encode_state=encode_state)

        return encode_state.coded_message

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.response = self

        super()._resolve_snrefs(context)

        context.response = None
