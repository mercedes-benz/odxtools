# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Optional, overload
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkRef
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class DynEndDopRef(OdxLinkRef):
    termination_value_raw: str

    @staticmethod
    @overload
    def from_et(et_element: None, context: OdxDocContext) -> None:
        ...

    @staticmethod
    @overload
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DynEndDopRef":
        ...

    @staticmethod
    def from_et(et_element: ElementTree.Element | None,
                context: OdxDocContext) -> Optional["DynEndDopRef"]:

        if et_element is None:
            odxraise("Mandatory DYN-END-DOP-REF tag is missing")
            return None

        kwargs = dataclass_fields_asdict(OdxLinkRef.from_et(et_element, context))

        termination_value_raw = odxrequire(et_element.findtext("TERMINATION-VALUE"))

        return DynEndDopRef(termination_value_raw=termination_value_raw, **kwargs)
