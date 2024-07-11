# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import ParameterType
from .parameterwithdop import ParameterWithDOP


@dataclass
class SystemParameter(ParameterWithDOP):
    sysparam: str

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SystemParameter":

        kwargs = dataclass_fields_asdict(ParameterWithDOP.from_et(et_element, doc_frags))

        sysparam = odxrequire(et_element.get("SYSPARAM"))

        return SystemParameter(sysparam=sysparam, **kwargs)

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "SYSTEM"

    @property
    @override
    def is_required(self) -> bool:
        raise NotImplementedError("SystemParameter.is_required is not implemented yet.")

    @property
    @override
    def is_settable(self) -> bool:
        raise NotImplementedError("SystemParameter.is_settable is not implemented yet.")

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        raise NotImplementedError("Encoding a SystemParameter is not implemented yet.")

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        raise NotImplementedError("Decoding SystemParameter is not implemented yet.")
