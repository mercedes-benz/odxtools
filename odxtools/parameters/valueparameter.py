# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from typing_extensions import override

from ..dataobjectproperty import DataObjectProperty
from ..encodestate import EncodeState
from ..exceptions import EncodeError, odxraise, odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType, ParameterValue
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP


@dataclass(kw_only=True)
class ValueParameter(ParameterWithDOP):
    physical_default_value_raw: str | None = None

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "VALUE"

    @property
    def physical_default_value(self) -> AtomicOdxType | None:
        return self._physical_default_value

    @property
    @override
    def is_required(self) -> bool:
        return self._physical_default_value is None

    @property
    @override
    def is_settable(self) -> bool:
        return True

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ValueParameter":

        kwargs = dataclass_fields_asdict(ParameterWithDOP.from_et(et_element, context))

        physical_default_value_raw = et_element.findtext("PHYSICAL-DEFAULT-VALUE")

        return ValueParameter(physical_default_value_raw=physical_default_value_raw, **kwargs)

    def __post_init__(self) -> None:
        self._physical_default_value: AtomicOdxType | None = None

    @override
    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    @override
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        if self.physical_default_value_raw is not None:
            dop = odxrequire(self.dop)
            if not isinstance(dop, DataObjectProperty):
                odxraise("Value parameters can only define a physical default "
                         "value if they use a simple DOP")
            base_data_type = dop.physical_type.base_data_type
            self._physical_default_value = base_data_type.from_string(
                self.physical_default_value_raw)

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:

        if physical_value is None:
            physical_value = self._physical_default_value
        if physical_value is None:
            odxraise(
                f"A value for parameter '{self.short_name}' must be specified"
                f" because the parameter does not exhibit a default.", EncodeError)

        self.dop.encode_into_pdu(physical_value, encode_state=encode_state)
