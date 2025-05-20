# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .configitem import ConfigItem
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SystemItem(ConfigItem):
    """This class represents a SYSTEM-ITEM."""

    sysparam: str

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SystemItem":
        kwargs = dataclass_fields_asdict(ConfigItem.from_et(et_element, context))

        sysparam = odxrequire(et_element.attrib.get("SYSPARAM"))

        return SystemItem(sysparam=sysparam, **kwargs)
