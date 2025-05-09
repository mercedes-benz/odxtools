# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxraise
from .identvaluetype import IdentValueType
from .odxdoccontext import OdxDocContext


@dataclass(kw_only=True)
class IdentValue:
    """
    Corresponds to IDENT-VALUE.
    """

    value: str

    # note that the spec says this attribute is named "TYPE", but in
    # python, "type" is a build-in function...
    value_type: IdentValueType

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "IdentValue":
        value = et_element.text or ""

        try:
            value_type = IdentValueType(et_element.attrib["TYPE"])
        except Exception as e:
            odxraise(f"Cannot parse IDENT-VALUE-TYPE: {e}")
            value_type = None

        return IdentValue(value=value, value_type=value_type)
