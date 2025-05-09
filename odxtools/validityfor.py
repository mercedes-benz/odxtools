# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .sessionsubelemtype import SessionSubElemType


@dataclass(kw_only=True)
class ValidityFor:
    value: str
    value_type: SessionSubElemType

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ValidityFor":
        value = et_element.text or ""

        value_type_str = odxrequire(et_element.get("TYPE"))
        try:
            value_type = SessionSubElemType(value_type_str)
        except ValueError:
            value_type = cast(SessionSubElemType, None)
            odxraise(f"Encountered unknown SESSION-SUB-ELEM-TYPE type '{value_type_str}'")

        return ValidityFor(
            value=value,
            value_type=value_type,
        )
