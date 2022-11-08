# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc
from typing import cast, List, Dict, Optional, Any, Union
from dataclasses import dataclass

from .utils import read_description_from_odx
from .physicaltype import PhysicalType, read_physical_type_from_odx
from .globals import logger
from .compumethods import CompuMethod, read_compu_method_from_odx
from .units import Unit
from .diagcodedtypes import DiagCodedType, StandardLengthType, read_diag_coded_type_from_odx
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError
from .odxlink import OdxLinkRef, OdxLinkId, OdxDocFragment, OdxLinkDatabase

class DopBase(abc.ABC):
    """ Base class for all DOPs.

    Any class that a parameter can reference via a DOP-REF should inherit from this class.
    """

    def __init__(self,
                 odx_id,
                 short_name,
                 long_name=None,
                 description=None,
                 is_visible=True):
        self.odx_id = odx_id
        self.short_name = short_name
        self.long_name = long_name
        self.description = description
        self.is_visible = is_visible

    @abc.abstractmethod
    def convert_physical_to_bytes(self, physical_value, encode_state: EncodeState, bit_position: int) -> bytes:
        """Convert the physical value into bytes."""
        pass

    @abc.abstractmethod
    def convert_bytes_to_physical(self, decode_state: DecodeState, bit_position: int = 0):
        """Extract the bytes from the PDU and convert them to the physical value."""
        pass


class DataObjectProperty(DopBase):
    """This class represents a DATA-OBJECT-PROP."""

    def __init__(self,
                 odx_id: OdxLinkId,
                 short_name: str,
                 diag_coded_type: DiagCodedType,
                 physical_type: PhysicalType,
                 compu_method: CompuMethod,
                 unit_ref: Optional[OdxLinkRef] = None,
                 long_name: Optional[str] = None,
                 description: Optional[str] = None
                 ):
        super().__init__(odx_id=odx_id,
                         short_name=short_name,
                         long_name=long_name,
                         description=description)
        self.diag_coded_type = diag_coded_type
        self.physical_type = physical_type
        self.compu_method = compu_method
        self.unit_ref = unit_ref
        self._unit = None

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

    def convert_physical_to_internal(self, physical_value):
        assert self.physical_type.base_data_type.isinstance(physical_value),\
            f"Expected {self.physical_type.base_data_type.value}, got {type(physical_value)}"

        return self.compu_method.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(self, physical_value, encode_state, bit_position):
        if not self.is_valid_physical_value(physical_value):
            raise EncodeError(f"The value {repr(physical_value)} of type {type(physical_value)}"
                              f" is not a valid." +
                              (f" Valid values are {self.compu_method.get_valid_physical_values()}"
                               if self.compu_method.get_valid_physical_values()
                               else f" Expected type {self.physical_type.base_data_type.value}.")
                              )

        internal_val = self.convert_physical_to_internal(physical_value)
        return self.diag_coded_type.convert_internal_to_bytes(internal_val, encode_state, bit_position=bit_position)

    def convert_bytes_to_physical(self, decode_state, bit_position: int = 0):
        assert 0 <= bit_position and bit_position < 8

        internal, next_byte_position = self.diag_coded_type.convert_bytes_to_internal(decode_state,
                                                                                      bit_position=bit_position)

        if self.compu_method.is_valid_internal_value(internal):
            return self.compu_method.convert_internal_to_physical(internal), next_byte_position
        else:
            # TODO: How to prevent this?
            raise DecodeError(f"DOP {self.short_name} could not convert the coded value "
                              f" {repr(internal)} to physical type {self.physical_type.base_data_type}.")

    def is_valid_physical_value(self, physical_value):
        return self.compu_method.is_valid_physical_value(physical_value)

    def get_valid_physical_values(self):
        return self.compu_method.get_valid_physical_values()

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        """Resolves the reference to the unit"""
        if self.unit_ref:
            self._unit = odxlinks.resolve(self.unit_ref)

    def __repr__(self) -> str:
        return \
            f"DataObjectProperty('{self.short_name}', " + \
            ", ".join([
                f"category='{self.compu_method.category}'",
                f"internal_type='{self.diag_coded_type}'",
                f"physical_type={self.physical_type}",
                f"unit_ref='{self.unit_ref}'",
            ]) + \
            ")"

    def __str__(self) -> str:
        return \
            f"DataObjectProperty('{self.short_name}', " + \
            ", ".join([
                f"category='{self.compu_method.category}'",
                f"diag_coded_type='{self.diag_coded_type}'",
                f"physical_type={self.physical_type}",
                f"unit_ref='{self.unit_ref}'",
            ]) + \
            ")"


@dataclass
class DiagnosticTroubleCode:
    trouble_code: int
    odx_id: Optional[OdxLinkId] = None
    short_name: Optional[str] = None
    text: Optional[str] = None
    display_trouble_code: Optional[str] = None
    level: Union[bytes, bytearray, None] = None
    is_temporary: bool = False


class DtcRef:
    """A proxy for DiagnosticTroubleCode.
    The DTC is referenced by ID and the ID-REF
    is resolved after loading the pdx database.
    """

    def __init__(self, dtc_ref: OdxLinkRef):
        self.dtc_ref = dtc_ref
        self.dtc: Optional[DiagnosticTroubleCode] = None

    @property
    def odx_id(self):
        return self.dtc.odx_id

    @property
    def short_name(self):
        return self.dtc.short_name

    @property
    def trouble_code(self):
        return self.dtc.trouble_code

    @property
    def text(self):
        return self.dtc.text

    @property
    def display_trouble_code(self):
        return self.dtc.display_trouble_code

    @property
    def level(self):
        return self.dtc.level

    @property
    def is_temporary(self):
        return self.dtc.is_temporary

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        self.dtc: Optional[DiagnosticTroubleCode] = odxlinks.resolve(self.dtc_ref) # type: ignore

        assert isinstance(self.dtc, DiagnosticTroubleCode),\
            f"DTC-REF {self.dtc_ref} does not reference a DTC but a {type(self.dtc)}."


class DtcDop(DataObjectProperty):
    """ A DOP describing a diagnostic trouble code """

    def __init__(self,
                 odx_id: OdxLinkId,
                 short_name: str,
                 diag_coded_type: DiagCodedType,
                 physical_type: PhysicalType,
                 compu_method: CompuMethod,
                 dtcs: List[Union[DiagnosticTroubleCode, DtcRef]],
                 is_visible: bool = False,
                 linked_dtc_dops: bool = False,
                 long_name: Optional[str] = None,
                 description: Optional[str] = None
                 ):
        super().__init__(odx_id=odx_id,
                         short_name=short_name,
                         long_name=long_name,
                         description=description,
                         diag_coded_type=diag_coded_type,
                         physical_type=physical_type,
                         compu_method=compu_method)
        self.dtcs = dtcs
        self.is_visible = is_visible
        self.linked_dtc_dops = linked_dtc_dops

    def convert_bytes_to_physical(self, decode_state, bit_position: int = 0):
        trouble_code, next_byte = \
            super().convert_bytes_to_physical(decode_state,
                                              bit_position=bit_position)

        dtcs = [ x for x in self.dtcs if x.trouble_code == trouble_code ]

        assert len(dtcs) < 2, \
            f"Multiple matching DTCs for trouble code 0x{trouble_code:06x}"

        if len(dtcs) == 1:
            # we found exactly one described DTC
            return dtcs[0], next_byte

        # the DTC was not specified. This probably means that the
        # diagnostic description file is incomplete. We do not bail
        # out but we cannot provide an interpretation for it out of the
        # box...
        dtc = DiagnosticTroubleCode(trouble_code=trouble_code)

        return dtc, next_byte

    def convert_physical_to_bytes(self, physical_value, encode_state, bit_position):
        if isinstance(physical_value, DiagnosticTroubleCode):
            trouble_code = physical_value.trouble_code
        elif isinstance(physical_value, int):
            # assume that physical value is the trouble_code
            trouble_code = physical_value
        elif isinstance(physical_value, str):
            # assume that physical value is the short_name
            dtc = next(filter(lambda dtc: dtc.short_name == physical_value,
                              self.dtcs))
            trouble_code = dtc.trouble_code
        else:
            raise EncodeError(f"The DTC-DOP {self.short_name} expected a"
                              f" DiagnosticTroubleCode but got {physical_value}.")

        return super().convert_physical_to_bytes(trouble_code, encode_state, bit_position)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        odxlinks[self.odx_id] = self
        for dtc in self.dtcs:
            if isinstance(dtc, DiagnosticTroubleCode):
                assert dtc.odx_id is not None
                odxlinks[dtc.odx_id] = dtc
        return odxlinks

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        for dtc in self.dtcs:
            if isinstance(dtc, DtcRef):
                dtc._resolve_references(odxlinks)


def read_dtc_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    if et_element.find("DISPLAY-TROUBLE-CODE") is not None:
        display_trouble_code = et_element.find("DISPLAY-TROUBLE-CODE").text
    else:
        display_trouble_code = None

    if et_element.find("LEVEL") is not None:
        level = et_element.find("LEVEL").text
    else:
        level = None

    return DiagnosticTroubleCode(odx_id=OdxLinkId.from_et(et_element, doc_frags),
                                 short_name=et_element.find("SHORT-NAME").text,
                                 trouble_code=int(
                                     et_element.find("TROUBLE-CODE").text),
                                 text=et_element.find("TEXT").text,
                                 display_trouble_code=display_trouble_code,
                                 level=level)


def read_data_object_property_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
    -> DataObjectProperty:
    """Reads a DATA-OBJECT-PROP or a DTC-DOP."""
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    logger.debug('Parsing DOP ' + short_name)

    diag_coded_type = read_diag_coded_type_from_odx(
        et_element.find("DIAG-CODED-TYPE"), doc_frags)

    physical_type = read_physical_type_from_odx(
        et_element.find("PHYSICAL-TYPE"), doc_frags)
    compu_method = read_compu_method_from_odx(et_element.find(
        "COMPU-METHOD"), doc_frags, diag_coded_type.base_data_type, physical_type.base_data_type)

    if et_element.tag == "DATA-OBJECT-PROP":
        unit_ref = OdxLinkRef.from_et(et_element.find("UNIT-REF"), doc_frags)
        dop = DataObjectProperty(odx_id,
                                 short_name,
                                 diag_coded_type,
                                 physical_type,
                                 compu_method,
                                 unit_ref=unit_ref,
                                 long_name=long_name,
                                 description=description)
    else:
        dtcs = [read_dtc_from_odx(el, doc_frags)
                for el in et_element.iterfind("DTCS/DTC")]
        dtcs += [DtcRef(cast(OdxLinkRef, OdxLinkRef.from_et(el, doc_frags)))
                 for el in et_element.iterfind("DTCS/DTC-REF")]

        is_visible = et_element.get("IS-VISIBLE") == "true"
        dop = DtcDop(odx_id,
                     short_name,
                     diag_coded_type,
                     physical_type,
                     compu_method,
                     dtcs,
                     is_visible=is_visible,
                     long_name=long_name,
                     description=description)
    return dop
