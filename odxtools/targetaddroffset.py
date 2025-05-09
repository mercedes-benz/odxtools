# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .odxdoccontext import OdxDocContext


@dataclass(kw_only=True)
class TargetAddrOffset:

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "TargetAddrOffset":
        return TargetAddrOffset()
