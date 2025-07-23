# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .infocomponent import InfoComponent
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class Oem(InfoComponent):

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Oem":
        kwargs = dataclass_fields_asdict(InfoComponent.from_et(et_element, context))

        return Oem(**kwargs)
