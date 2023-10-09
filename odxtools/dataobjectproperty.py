# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast
from xml.etree import ElementTree

from .compumethods.compumethod import CompuMethod
from .compumethods.createanycompumethod import create_any_compu_method_from_et
from .createanydiagcodedtype import create_any_diag_coded_type_from_et
from .createsdgs import create_sdgs_from_et
from .decodestate import DecodeState
from .diagcodedtype import DiagCodedType
from .diagnostictroublecode import DiagnosticTroubleCode
from .dopbase import DopBase
from .element import IdentifiableElement
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import AtomicOdxType, ParameterValue, odxstr_to_bool
from .physicaltype import PhysicalType
from .unit import Unit
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DataObjectProperty(DopBase):
    """This class represents a DATA-OBJECT-PROP."""

    diag_coded_type: DiagCodedType
    physical_type: PhysicalType
    compu_method: CompuMethod
    unit_ref: Optional[OdxLinkRef]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DataObjectProperty":
        """Reads a DATA-OBJECT-PROP or a DTC-DOP."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))

        diag_coded_type = create_any_diag_coded_type_from_et(
            odxrequire(et_element.find("DIAG-CODED-TYPE")), doc_frags)

        physical_type = PhysicalType.from_et(
            odxrequire(et_element.find("PHYSICAL-TYPE")), doc_frags)
        compu_method = create_any_compu_method_from_et(
            odxrequire(et_element.find("COMPU-METHOD")),
            doc_frags,
            diag_coded_type.base_data_type,
            physical_type.base_data_type,
        )
        unit_ref = OdxLinkRef.from_et(et_element.find("UNIT-REF"), doc_frags)

        if et_element.tag == "DATA-OBJECT-PROP":
            dop = DataObjectProperty(
                is_visible_raw=is_visible_raw,
                diag_coded_type=diag_coded_type,
                physical_type=physical_type,
                compu_method=compu_method,
                unit_ref=unit_ref,
                sdgs=sdgs,
                **kwargs)
        else:
            dtclist: List[Union[DiagnosticTroubleCode, OdxLinkRef]] = []
            if (dtcs_elem := et_element.find("DTCS")) is not None:
                for dtc_proxy_elem in dtcs_elem:
                    if dtc_proxy_elem.tag == "DTC":
                        dtclist.append(DiagnosticTroubleCode.from_et(dtc_proxy_elem, doc_frags))
                    elif dtc_proxy_elem.tag == "DTC-REF":
                        dtclist.append(OdxLinkRef.from_et(dtc_proxy_elem, doc_frags))

            # TODO: NOT-INHERITED-DTC-SNREFS
            linked_dtc_dop_refs = [
                cast(OdxLinkRef, OdxLinkRef.from_et(dtc_ref_elem, doc_frags))
                for dtc_ref_elem in et_element.iterfind("LINKED-DTC-DOPS/"
                                                        "LINKED-DTC-DOP/"
                                                        "DTC-DOP-REF")
            ]

            from .dtcdop import DtcDop

            dop = DtcDop(
                diag_coded_type=diag_coded_type,
                physical_type=physical_type,
                compu_method=compu_method,
                unit_ref=unit_ref,
                dtcs_raw=dtclist,
                linked_dtc_dop_refs=linked_dtc_dop_refs,
                is_visible_raw=is_visible_raw,
                sdgs=sdgs,
                **kwargs)
        return dop

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()
        result.update(self.diag_coded_type._build_odxlinks())
        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Resolves the reference to the unit"""
        super()._resolve_odxlinks(odxlinks)

        self.diag_coded_type._resolve_odxlinks(odxlinks)

        self._unit: Optional[Unit] = None
        if self.unit_ref:
            self._unit = odxlinks.resolve(self.unit_ref, Unit)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        self.diag_coded_type._resolve_snrefs(diag_layer)

    @property
    def unit(self) -> Optional[Unit]:
        return self._unit

    def get_static_bit_length(self) -> Optional[int]:
        return self.diag_coded_type.get_static_bit_length()

    def convert_physical_to_internal(self, physical_value: Any) -> Any:
        """
        Convert a physical representation of a parameter to its internal counterpart
        """
        odxassert(
            self.physical_type.base_data_type.isinstance(physical_value),
            f"Expected {self.physical_type.base_data_type.value}, got {type(physical_value)}")

        return self.compu_method.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(self, physical_value: Any, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        """
        Convert a physical representation of a parameter to a string bytes that can be send over the wire
        """
        if not self.is_valid_physical_value(physical_value):
            raise EncodeError(f"The value {repr(physical_value)} of type {type(physical_value)}"
                              f" is not a valid.")

        internal_val = self.convert_physical_to_internal(physical_value)
        return self.diag_coded_type.convert_internal_to_bytes(
            internal_val, encode_state, bit_position=bit_position)

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[Any, int]:
        """
        Convert the internal representation of a value into its physical value.

        Returns a (physical_value, start_position_of_next_parameter) tuple.
        """
        odxassert(0 <= bit_position and bit_position < 8)

        internal, cursor_position = self.diag_coded_type.convert_bytes_to_internal(
            decode_state, bit_position=bit_position)

        if self.compu_method.is_valid_internal_value(internal):
            return self.compu_method.convert_internal_to_physical(internal), cursor_position
        else:
            # TODO: How to prevent this?
            raise DecodeError(
                f"DOP {self.short_name} could not convert the coded value "
                f" {repr(internal)} to physical type {self.physical_type.base_data_type}.")

    def is_valid_physical_value(self, physical_value: ParameterValue) -> bool:
        return self.compu_method.is_valid_physical_value(cast(AtomicOdxType, physical_value))
