# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .basefunctionnode import BaseFunctionNode
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class FunctionNode(BaseFunctionNode):

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "FunctionNode":
        kwargs = dataclass_fields_asdict(BaseFunctionNode.from_et(et_element, context))

        return FunctionNode(**kwargs)
