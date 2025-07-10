# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .logicallink import LogicalLink
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class GatewayLogicalLink(LogicalLink):
    semantic: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "GatewayLogicalLink":
        kwargs = dataclass_fields_asdict(LogicalLink.from_et(et_element, context))

        semantic = et_element.findtext("SEMANTIC")

        return GatewayLogicalLink(semantic=semantic, **kwargs)
