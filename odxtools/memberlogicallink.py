# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .logicallink import LogicalLink
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class MemberLogicalLink(LogicalLink):

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MemberLogicalLink":
        kwargs = dataclass_fields_asdict(LogicalLink.from_et(et_element, context))

        return MemberLogicalLink(**kwargs)
