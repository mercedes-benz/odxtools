# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .odxlink import OdxDocFragment
from .odxtypes import odxstr_to_bool
from .utils import dataclass_fields_asdict


@dataclass
class Structure(BasicStructure):
    is_visible_raw: bool | None

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw in (True, None)

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: list[OdxDocFragment]) -> "Structure":
        """Read a STRUCTURE element from XML."""
        kwargs = dataclass_fields_asdict(BasicStructure.from_et(et_element, doc_frags))

        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))

        return Structure(is_visible_raw=is_visible_raw, **kwargs)
