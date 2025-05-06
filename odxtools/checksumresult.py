from dataclasses import dataclass
from typing import cast
from xml.etree import ElementTree

from .exceptions import odxraise
from .odxdoccontext import OdxDocContext
from .sessionsubelemtype import SessionSubElemType


@dataclass(kw_only=True)
class ChecksumResult:
    value: str
    checksum_type: SessionSubElemType | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ChecksumResult":
        value = et_element.text or ""

        if (checksum_type_str := et_element.get("TYPE")) is not None:
            try:
                checksum_type = SessionSubElemType(checksum_type_str)
            except ValueError:
                checksum_type = cast(SessionSubElemType, None)
                odxraise(f"Encountered unknown SESSION-SUB-ELEM-TYPE type '{checksum_type_str}'")

        return ChecksumResult(value=value, checksum_type=checksum_type)

    @staticmethod
    def from_string(value: str) -> "ChecksumResult":
        return ChecksumResult(value=value, checksum_type=None)

    def __str__(self) -> str:
        return self.value
