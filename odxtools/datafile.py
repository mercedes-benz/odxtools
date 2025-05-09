# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxtypes import odxstr_to_bool


@dataclass(kw_only=True)
class Datafile:
    value: str
    latebound_datafile: bool

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Datafile":
        value = et_element.text or ""
        latebound_datafile = odxrequire(odxstr_to_bool(et_element.attrib.get("LATEBOUND-DATAFILE")))

        return Datafile(
            value=value,
            latebound_datafile=latebound_datafile,
        )
