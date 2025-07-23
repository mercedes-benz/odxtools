from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from .encryptcompressmethodtype import EncryptCompressMethodType
from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .odxtypes import AtomicOdxType, DataType
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class EncryptCompressMethod:
    value_raw: str
    value_type: EncryptCompressMethodType

    @property
    def value(self) -> AtomicOdxType:
        return self._value

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EncryptCompressMethod":
        value_raw = et_element.text or ""

        value_type_str = odxrequire(et_element.attrib.get("TYPE"))
        try:
            value_type = EncryptCompressMethodType(value_type_str)
        except ValueError:
            value_type = cast(EncryptCompressMethodType, None)
            odxraise(f"Encountered unknown addressing type '{value_type_str}'")

        return EncryptCompressMethod(value_raw=value_raw, value_type=value_type)

    def __post_init__(self) -> None:
        self._data_type = DataType(self.value_type.value)
        self._value = self._data_type.from_string(self.value_raw.strip())

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
