# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .odxlink import OdxDocFragment
from .utils import dataclass_fields_asdict


@dataclass
class Structure(BasicStructure):

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Structure":
        """Read a STRUCTURE element from XML."""
        kwargs = dataclass_fields_asdict(BasicStructure.from_et(et_element, doc_frags))

        return Structure(**kwargs)
