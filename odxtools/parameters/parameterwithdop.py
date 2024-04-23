# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from typing_extensions import override

from ..dataobjectproperty import DataObjectProperty
from ..decodestate import DecodeState
from ..dopbase import DopBase
from ..dtcdop import DtcDop
from ..encodestate import EncodeState
from ..exceptions import odxassert, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..odxtypes import AtomicOdxType, ParameterValue
from ..physicaltype import PhysicalType
from ..utils import dataclass_fields_asdict
from .parameter import Parameter

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class ParameterWithDOP(Parameter):
    dop_ref: Optional[OdxLinkRef]
    dop_snref: Optional[str]

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ParameterWithDOP":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        dop_ref = OdxLinkRef.from_et(et_element.find("DOP-REF"), doc_frags)
        dop_snref = None
        if (dop_snref_elem := et_element.find("DOP-SNREF")) is not None:
            dop_snref = odxrequire(dop_snref_elem.get("SHORT-NAME"))

        return ParameterWithDOP(dop_ref=dop_ref, dop_snref=dop_snref, **kwargs)

    def __post_init__(self) -> None:
        odxassert(self.dop_snref is not None or self.dop_ref is not None,
                  f"Param {self.short_name} without a DOP-(SN)REF should not exist!")
        self._dop: Optional[DopBase] = None

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.dop_ref is not None:
            odxassert(self.dop_snref is None)
            # TODO: do not do lenient resolves here. The problem is
            # that currently not all kinds of DOPs are internalized
            # (e.g., static and dynamic fields)
            self._dop = odxlinks.resolve_lenient(self.dop_ref)

    @override
    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        if self.dop_snref:
            ddds = diag_layer.diag_data_dictionary_spec
            self._dop = odxrequire(ddds.all_data_object_properties.get(self.dop_snref))

    @property
    def dop(self) -> DopBase:
        """may be a DataObjectProperty, a Structure or None"""

        return odxrequire(
            self._dop, "Specifying a data object property is mandatory but it "
            "could not be resolved")

    @override
    def get_static_bit_length(self) -> Optional[int]:
        if self._dop is not None:
            return self._dop.get_static_bit_length()
        else:
            return None

    @property
    def physical_type(self) -> Optional[PhysicalType]:
        if isinstance(self.dop, (DataObjectProperty, DtcDop)):
            return self.dop.physical_type
        else:
            return None

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        self.dop.encode_into_pdu(cast(AtomicOdxType, physical_value), encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        return self.dop.decode_from_pdu(decode_state)
