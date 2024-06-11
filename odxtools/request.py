# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .encodestate import EncodeState
from .odxlink import OdxDocFragment
from .odxtypes import ParameterValue
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


# TODO: The spec does not say that requests are basic structures. For
# now, we derive from it anyway because it simplifies the en- and
# decoding machinery...
@dataclass
class Request(BasicStructure):

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Request":
        """Reads a response."""
        kwargs = dataclass_fields_asdict(BasicStructure.from_et(et_element, doc_frags))

        return Request(**kwargs)

    def encode(self, **kwargs: ParameterValue) -> bytes:
        encode_state = EncodeState(is_end_of_pdu=True)

        self.encode_into_pdu(physical_value=kwargs, encode_state=encode_state)

        return encode_state.coded_message

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.request = self

        super()._resolve_snrefs(context)

        context.request = None
