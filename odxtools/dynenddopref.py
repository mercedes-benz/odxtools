# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional, overload
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkRef
from .utils import dataclass_fields_asdict


@dataclass
class DynEndDopRef(OdxLinkRef):
    termination_value_raw: str

    @staticmethod
    @overload
    def from_et(et_element: None, source_doc_frags: List[OdxDocFragment]) -> None:
        ...

    @staticmethod
    @overload
    def from_et(et_element: ElementTree.Element,
                source_doc_frags: List[OdxDocFragment]) -> "DynEndDopRef":
        ...

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                source_doc_frags: List[OdxDocFragment]) -> Optional["DynEndDopRef"]:

        if et_element is None:
            odxraise("Mandatory DYN-END-DOP-REF tag is missing")
            return None

        kwargs = dataclass_fields_asdict(OdxLinkRef.from_et(et_element, source_doc_frags))

        termination_value_raw = odxrequire(et_element.findtext("TERMINATION-VALUE"))

        return DynEndDopRef(termination_value_raw=termination_value_raw, **kwargs)
