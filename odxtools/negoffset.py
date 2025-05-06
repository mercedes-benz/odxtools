# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .targetaddroffset import TargetAddrOffset
from .utils import dataclass_fields_asdict, read_hex_binary


@dataclass(kw_only=True)
class NegOffset(TargetAddrOffset):
    negative_offset: int

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "NegOffset":
        kwargs = dataclass_fields_asdict(TargetAddrOffset.from_et(et_element, context))

        negative_offset = odxrequire(read_hex_binary(et_element.find("NEGATIVE-OFFSET")))

        return NegOffset(negative_offset=negative_offset, **kwargs)
