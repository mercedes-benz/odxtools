# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .odxlink import OdxDocFragment
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
