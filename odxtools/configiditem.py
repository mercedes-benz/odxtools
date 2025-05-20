# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .configitem import ConfigItem
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ConfigIdItem(ConfigItem):
    """This class represents a CONFIG-ID-ITEM."""

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ConfigIdItem":
        kwargs = dataclass_fields_asdict(ConfigItem.from_et(et_element, context))

        return ConfigIdItem(**kwargs)
