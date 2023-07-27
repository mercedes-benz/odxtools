# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

from .compumethods import CompuMethod, create_any_compu_method_from_et
from .decodestate import DecodeState
from .diagcodedtypes import DiagCodedType, StandardLengthType, create_any_diag_coded_type_from_et
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError
from .globals import logger
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .physicaltype import PhysicalType
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .units import Unit
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DopBase:
    """Base class for all DOPs.

    Any class that a parameter can reference via a DOP-REF should inherit from this class.
    """

    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    is_visible_raw: Optional[bool]
    sdgs: List[SpecialDataGroup]

    def __hash__(self) -> int:
        result = 0

        result += hash(self.short_name)
        result += hash(self.long_name)
        result += hash(self.description)
        result += hash(self.is_visible_raw)

        return result

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw in (None, True)

    def convert_physical_to_bytes(self, physical_value, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        """Convert the physical value into bytes."""
        raise NotImplementedError

    def convert_bytes_to_physical(self, decode_state: DecodeState, bit_position: int = 0):
        """Extract the bytes from the PDU and convert them to the physical value."""
        raise NotImplementedError


class DataObjectProperty(DopBase):
    """This class represents a DATA-OBJECT-PROP."""

    def __init__(
        self,
        *,
        diag_coded_type: DiagCodedType,
        physical_type: PhysicalType,
        compu_method: CompuMethod,
        unit_ref: Optional[OdxLinkRef],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.diag_coded_type = diag_coded_type
        self.physical_type = physical_type
        self.compu_method = compu_method
        self.unit_ref = unit_ref

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "DataObjectProperty":
        """Reads a DATA-OBJECT-PROP or a DTC-DOP."""
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))

        diag_coded_type = create_any_diag_coded_type_from_et(
            et_element.find("DIAG-CODED-TYPE"), doc_frags)

        physical_type = PhysicalType.from_et(et_element.find("PHYSICAL-TYPE"), doc_frags)
        compu_method = create_any_compu_method_from_et(
            et_element.find("COMPU-METHOD"),
            doc_frags,
            diag_coded_type.base_data_type,
            physical_type.base_data_type,
        )
        unit_ref = OdxLinkRef.from_et(et_element.find("UNIT-REF"), doc_frags)

        if et_element.tag == "DATA-OBJECT-PROP":
            dop = DataObjectProperty(
                odx_id=odx_id,
                short_name=short_name,
                long_name=long_name,
                description=description,
                is_visible_raw=is_visible_raw,
                diag_coded_type=diag_coded_type,
                physical_type=physical_type,
                compu_method=compu_method,
                unit_ref=unit_ref,
                sdgs=sdgs,
            )
        else:
            dtclist: List[Union[DiagnosticTroubleCode, OdxLinkRef]] = list()
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

            dop = DtcDop(
                odx_id=odx_id,
                short_name=short_name,
                long_name=long_name,
                description=description,
                diag_coded_type=diag_coded_type,
                physical_type=physical_type,
                compu_method=compu_method,
                unit_ref=unit_ref,
                dtcs_raw=dtclist,
                linked_dtc_dop_refs=linked_dtc_dop_refs,
                is_visible_raw=is_visible_raw,
                sdgs=sdgs,
            )
        return dop

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()
        result.update(self.diag_coded_type._build_odxlinks())
        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase):
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

    @property
    def bit_length(self):
        # TODO: The DiagCodedTypes except StandardLengthType don't have a bit length.
        #       Should we remove this bit_length property from DOP or return None?
        if isinstance(self.diag_coded_type, StandardLengthType):
            return self.diag_coded_type.bit_length
        else:
            return None

    def convert_physical_to_internal(self, physical_value: Any) -> Any:
        """
        Convert a physical representation of a parameter to its internal counterpart
        """
        assert self.physical_type.base_data_type.isinstance(
            physical_value
        ), f"Expected {self.physical_type.base_data_type.value}, got {type(physical_value)}"

        return self.compu_method.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(self, physical_value: Any, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        """
        Convert a physical representation of a parameter to a string bytes that can be send over the wire
        """
        if not self.is_valid_physical_value(physical_value):
            raise EncodeError(f"The value {repr(physical_value)} of type {type(physical_value)}"
                              f" is not a valid." +
                              (f" Valid values are {self.compu_method.get_valid_physical_values()}"
                               if self.compu_method.get_valid_physical_values(
                               ) else f" Expected type {self.physical_type.base_data_type.value}."))

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
        assert 0 <= bit_position and bit_position < 8

        internal, next_byte_position = self.diag_coded_type.convert_bytes_to_internal(
            decode_state, bit_position=bit_position)

        if self.compu_method.is_valid_internal_value(internal):
            return self.compu_method.convert_internal_to_physical(internal), next_byte_position
        else:
            # TODO: How to prevent this?
            raise DecodeError(
                f"DOP {self.short_name} could not convert the coded value "
                f" {repr(internal)} to physical type {self.physical_type.base_data_type}.")

    def is_valid_physical_value(self, physical_value):
        return self.compu_method.is_valid_physical_value(physical_value)

    def get_valid_physical_values(self):
        return self.compu_method.get_valid_physical_values()

    def __repr__(self) -> str:
        return (f"DataObjectProperty('{self.short_name}', " + ", ".join([
            f"category='{self.compu_method.category}'",
            f"internal_type='{self.diag_coded_type}'",
            f"physical_type={self.physical_type}",
            f"unit_ref='{self.unit_ref}'",
        ]) + ")")

    def __str__(self) -> str:
        return (f"DataObjectProperty('{self.short_name}', " + ", ".join([
            f"category='{self.compu_method.category}'",
            f"diag_coded_type='{self.diag_coded_type}'",
            f"physical_type={self.physical_type}",
            f"unit_ref='{self.unit_ref}'",
        ]) + ")")


@dataclass
class DiagnosticTroubleCode:
    trouble_code: int
    odx_id: Optional[OdxLinkId]
    short_name: Optional[str]
    text: Optional[str]
    display_trouble_code: Optional[str]
    level: Union[bytes, None]
    is_temporary_raw: Optional[bool]
    sdgs: List[SpecialDataGroup]

    @property
    def is_temporary(self) -> bool:
        return self.is_temporary_raw == True

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "DiagnosticTroubleCode":
        if et_element.find("DISPLAY-TROUBLE-CODE") is not None:
            display_trouble_code = et_element.findtext("DISPLAY-TROUBLE-CODE")
        else:
            display_trouble_code = None

        if et_element.find("LEVEL") is not None:
            level = et_element.findtext("LEVEL")
        else:
            level = None

        is_temporary_raw = odxstr_to_bool(et_element.get("IS-TEMPORARY"))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return DiagnosticTroubleCode(
            odx_id=OdxLinkId.from_et(et_element, doc_frags),
            short_name=et_element.findtext("SHORT-NAME"),
            trouble_code=int(et_element.findtext("TROUBLE-CODE")),
            text=et_element.findtext("TEXT"),
            display_trouble_code=display_trouble_code,
            level=level,
            is_temporary_raw=is_temporary_raw,
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        if self.odx_id is not None:
            result[self.odx_id] = self

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer"):
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)


class DtcDop(DataObjectProperty):
    """A DOP describing a diagnostic trouble code"""

    def __init__(
        self,
        *,
        dtcs_raw: List[Union[DiagnosticTroubleCode, OdxLinkRef]],
        linked_dtc_dop_refs: List[OdxLinkRef],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.dtcs_raw = dtcs_raw
        self.linked_dtc_dop_refs = linked_dtc_dop_refs

    @property
    def dtcs(self) -> NamedItemList[DiagnosticTroubleCode]:
        return self._dtcs

    @property
    def linked_dtc_dops(self) -> NamedItemList["DtcDop"]:
        return self._linked_dtc_dops

    def convert_bytes_to_physical(self, decode_state, bit_position: int = 0):
        trouble_code, next_byte = super().convert_bytes_to_physical(
            decode_state, bit_position=bit_position)

        dtcs = [x for x in self.dtcs if x.trouble_code == trouble_code]

        assert len(dtcs) < 2, f"Multiple matching DTCs for trouble code 0x{trouble_code:06x}"

        if len(dtcs) == 1:
            # we found exactly one described DTC
            return dtcs[0], next_byte

        # the DTC was not specified. This probably means that the
        # diagnostic description file is incomplete. We do not bail
        # out but we cannot provide an interpretation for it out of the
        # box...
        dtc = DiagnosticTroubleCode(
            trouble_code=trouble_code,
            odx_id=None,
            short_name=None,
            text=None,
            display_trouble_code=None,
            level=None,
            is_temporary_raw=None,
            sdgs=[],
        )

        return dtc, next_byte

    def convert_physical_to_bytes(self, physical_value, encode_state, bit_position):
        if isinstance(physical_value, DiagnosticTroubleCode):
            trouble_code = physical_value.trouble_code
        elif isinstance(physical_value, int):
            # assume that physical value is the trouble_code
            trouble_code = physical_value
        elif isinstance(physical_value, str):
            # assume that physical value is the short_name
            dtc = next(filter(lambda dtc: dtc.short_name == physical_value, self.dtcs))
            trouble_code = dtc.trouble_code
        else:
            raise EncodeError(f"The DTC-DOP {self.short_name} expected a"
                              f" DiagnosticTroubleCode but got {physical_value}.")

        return super().convert_physical_to_bytes(trouble_code, encode_state, bit_position)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                odxlinks.update(dtc_proxy._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase):
        super()._resolve_odxlinks(odxlinks)

        self._dtcs: NamedItemList[DiagnosticTroubleCode] = NamedItemList(short_name_as_id)
        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                self._dtcs.append(dtc_proxy)
            elif isinstance(dtc_proxy, OdxLinkRef):
                dtc = odxlinks.resolve(dtc_proxy, DiagnosticTroubleCode)
                self._dtcs.append(dtc)

        linked_dtc_dops = [odxlinks.resolve(x, DtcDop) for x in self.linked_dtc_dop_refs]
        self._linked_dtc_dops = NamedItemList(short_name_as_id, linked_dtc_dops)

    def _resolve_snrefs(self, diag_layer: "DiagLayer"):
        super()._resolve_snrefs(diag_layer)

        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                dtc_proxy._resolve_snrefs(diag_layer)
