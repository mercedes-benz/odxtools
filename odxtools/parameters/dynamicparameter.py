# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..odxlink import OdxDocFragment
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType


@dataclass
class DynamicParameter(Parameter):

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DynamicParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        return DynamicParameter(**kwargs)

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

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        raise NotImplementedError("Encoding DynamicParameter is not implemented yet.")

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        raise NotImplementedError("Decoding DynamicParameter is not implemented yet.")
