# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..odxdoccontext import OdxDocContext
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass(kw_only=True)
class DynamicParameter(Parameter):

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "DYNAMIC"

    @property
    @override
    def is_required(self) -> bool:
        raise NotImplementedError(".is_required for a DynamicParameter")

    @property
    @override
    def is_settable(self) -> bool:
        raise NotImplementedError(".is_settable for a DynamicParameter")

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DynamicParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, context))

        return DynamicParameter(**kwargs)

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:
        raise NotImplementedError("Encoding DynamicParameter is not implemented yet.")

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        raise NotImplementedError("Decoding DynamicParameter is not implemented yet.")
