# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from typing_extensions import override

from ..dataobjectproperty import DataObjectProperty
from ..decodestate import DecodeState
from ..dopbase import DopBase
from ..dtcdop import DtcDop
from ..encodestate import EncodeState
from ..exceptions import odxassert, odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from ..odxtypes import AtomicOdxType, ParameterValue
from ..physicaltype import PhysicalType
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from .parameter import Parameter


@dataclass(kw_only=True)
class ParameterWithDOP(Parameter):
    dop_ref: OdxLinkRef | None = None
    dop_snref: str | None = None

    @property
    def dop(self) -> DopBase:
        """This is usually a DataObjectProperty or a Structure object"""

        return self._dop

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ParameterWithDOP":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, context))

        dop_ref = OdxLinkRef.from_et(et_element.find("DOP-REF"), context)
        dop_snref = None
        if (dop_snref_elem := et_element.find("DOP-SNREF")) is not None:
            dop_snref = odxrequire(dop_snref_elem.get("SHORT-NAME"))

        return ParameterWithDOP(dop_ref=dop_ref, dop_snref=dop_snref, **kwargs)

    def __post_init__(self) -> None:
        odxassert(self.dop_snref is not None or self.dop_ref is not None,
                  f"Param {self.short_name} without a DOP-(SN)REF should not exist!")
        self._dop: DopBase

    @override
    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.dop_ref is not None:
            odxassert(self.dop_snref is None)
            self._dop = odxlinks.resolve(self.dop_ref)

    @override
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        if self.dop_snref:
            ddds = odxrequire(context.diag_layer).diag_data_dictionary_spec
            self._dop = resolve_snref(self.dop_snref, ddds.all_data_object_properties, DopBase)

    @override
    def get_static_bit_length(self) -> int | None:
        if self._dop is not None:
            return self._dop.get_static_bit_length()
        else:
            return None

    @property
    def physical_type(self) -> PhysicalType | None:
        if isinstance(self.dop, (DataObjectProperty, DtcDop)):
            return self.dop.physical_type
        else:
            return None

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:
        self.dop.encode_into_pdu(cast(AtomicOdxType, physical_value), encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        return self.dop.decode_from_pdu(decode_state)
