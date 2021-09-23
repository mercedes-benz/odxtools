# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import abc
from typing import List, Union
from dataclasses import dataclass
from .globals import logger
from .compumethods import CompuMethod, read_compu_method_from_odx
from .odxtypes import _odx_isinstance

from .diagcodedtypes import DiagCodedType, StandardLengthType, read_diag_coded_type_from_odx
from .exceptions import DecodeError


class DopBase(abc.ABC):
    """ Base class for all DOPs.

    Any class that a parameter can reference via a DOP-REF should inherit from this class.
    """

    def __init__(self,
                 id,
                 short_name,
                 long_name=None,
                 description=None,
                 is_visible=True):
        self.id = id
        self.short_name = short_name
        self.long_name = long_name
        self.description = description
        self.is_visible = is_visible

    @property
    @abc.abstractclassmethod
    def bit_length(self):
        pass

    @abc.abstractclassmethod
    def convert_physical_to_internal(self, physical_value):
        """Convert the physical value to the internal value."""
        pass

    @abc.abstractclassmethod
    def convert_physical_to_bytes(self, physical_value, bit_position: int):
        """Convert the physical value into bytes."""
        pass

    @abc.abstractclassmethod
    def convert_bytes_to_physical(self, byte_code: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        """Extract the bytes from the PDU and convert them to the physical value."""
        pass


class DataObjectProperty(DopBase):
    """This class represents a DATA-OBJECT-PROP."""

    def __init__(self,
                 id: str,
                 short_name: str,
                 diag_coded_type: DiagCodedType,
                 physical_data_type: str,
                 compu_method: CompuMethod,
                 long_name: str = None,
                 description: str = None
                 ):
        super().__init__(id=id,
                         short_name=short_name,
                         long_name=long_name,
                         description=description)
        self.diag_coded_type = diag_coded_type
        self.physical_data_type = physical_data_type
        self.compu_method = compu_method

    @property
    def bit_length(self):
        # assert self.diag_coded_type.bit_length is None or isinstance(
        #     self.diag_coded_type.bit_length, int)
        # TODO: Some DiagCodedTypes, e.g. MinMaxLengthType doesn't have a bit length.
        #       Remove bit length attribute from DOP or return None?
        return getattr(self.diag_coded_type, "bit_length", None)

    def convert_physical_to_internal(self, physical_value):
        assert _odx_isinstance(
            physical_value, self.physical_data_type), f"Expected {self.physical_data_type}, got {type(physical_value)}"

        return self.compu_method.convert_physical_to_internal(physical_value)

    def convert_physical_to_bytes(self, physical_value, bit_position):
        assert self.is_valid_physical_value(
            physical_value), f"value {physical_value} of type, {type(physical_value)} is not valid. Expected type {self.physical_data_type}"
        internal_val = self.convert_physical_to_internal(physical_value)
        if self.diag_coded_type.dct_type == "STANDARD-LENGTH-TYPE":
            return self.diag_coded_type.convert_internal_to_bytes(internal_val, bit_position=bit_position)
        else:
            raise NotImplementedError(
                f"The diag coded type {self.diag_coded_type.dct_type} is not implemented yet.")

    def convert_bytes_to_physical(self, byte_code: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        assert 0 <= bit_position and bit_position < 8

        internal, next_byte_position = self.diag_coded_type.convert_bytes_to_internal(byte_code,
                                                                                      byte_position=byte_position,
                                                                                      bit_position=bit_position)

        if self.compu_method.is_valid_internal_value(internal):
            return self.compu_method.convert_internal_to_physical(internal), next_byte_position
        else:
            # TODO: How to prevent this?
            raise DecodeError(
                f"DOP {self.short_name} could not convert coded value {internal} to physical type {self.physical_data_type}.")

    def is_valid_physical_value(self, physical_value):
        return self.compu_method.is_valid_physical_value(physical_value)

    def get_valid_physical_values(self):
        return self.compu_method.get_valid_physical_values()

    def __repr__(self) -> str:
        return \
            f"DataObjectProperty('{self.short_name}', " + \
            f"category='{self.compu_method.category}', " + \
            f"internal_type='{self.diag_coded_type.base_data_type}', " + \
            f"physical_type='{self.physical_data_type}')"

    def __str__(self) -> str:
        return \
            f"DataObjectProperty('{self.short_name}', " + \
            f"category='{self.compu_method.category}', " + \
            f"internal_type='{self.diag_coded_type.base_data_type}', " + \
            f"physical_type='{self.physical_data_type}')"


@dataclass
class DiagnosticTroubleCode:
    id: str
    short_name: str
    trouble_code: int
    text: str
    display_trouble_code: Union[str, None] = None
    level: Union[bytes, bytearray, None] = None
    is_temporary: bool = False


class DtcRef:
    """A proxy for DiagnosticTroubleCode.
    The DTC is referenced by ID and the ID-REF is resolved after parsing."""

    def __init__(self, dtc_id):
        self.dtc_id = dtc_id
        self.dtc = None

    @property
    def id(self):
        return self.dtc.id

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

    def _resolve_references(self, id_lookup):
        self.dtc = id_lookup[self.dtc_id]


class DtcDop(DataObjectProperty):
    """ A DOP describing a diagnostic trouble code """

    def __init__(self,
                 id: str,
                 short_name: str,
                 diag_coded_type: DiagCodedType,
                 physical_data_type: str,
                 compu_method: CompuMethod,
                 dtcs: List[Union[DiagnosticTroubleCode, DtcRef]],
                 is_visible=False,
                 linked_dtc_dops=False,
                 long_name: str = None,
                 description: str = None
                 ):
        super().__init__(id=id,
                         short_name=short_name,
                         long_name=long_name,
                         description=description,
                         diag_coded_type=diag_coded_type,
                         physical_data_type=physical_data_type,
                         compu_method=compu_method)
        self.dtcs = dtcs
        self.is_visible = is_visible
        self.linked_dtc_dops = linked_dtc_dops

    def convert_bytes_to_physical(self, byte_code: Union[bytes, bytearray], byte_position: int = 0, bit_position: int = 0):
        trouble_code, next_byte = super().convert_bytes_to_physical(byte_code,
                                                                    byte_position=byte_position,
                                                                    bit_position=bit_position)
        try:
            dtc = next(filter(lambda dtc: dtc.trouble_code == trouble_code,
                              self.dtcs))
        except:
            raise DecodeError(
                f"DTC-DOP {self.short_name} extracted value {trouble_code} from PDU but it does not match any specified trouble codes.")
        return dtc, next_byte

    def _build_id_lookup(self):
        id_lookup = {}
        id_lookup[self.id] = self
        for dtc in self.dtcs:
            if isinstance(dtc, DiagnosticTroubleCode):
                id_lookup[dtc.id] = dtc
        return id_lookup

    def _resolve_references(self, id_lookup):
        for dtc in self.dtcs:
            if isinstance(dtc, DtcRef):
                dtc._resolve_references(id_lookup)


def read_dtc_from_odx(et_element):
    if et_element.find("DISPLAY-TROUBLE-CODE") is not None:
        display_trouble_code = et_element.find("DISPLAY-TROUBLE-CODE").text
    else:
        display_trouble_code = None

    if et_element.find("LEVEL") is not None:
        level = et_element.find("LEVEL").text
    else:
        level = None

    return DiagnosticTroubleCode(id=et_element.get("ID"),
                                 short_name=et_element.find("SHORT-NAME").text,
                                 trouble_code=int(
                                     et_element.find("TROUBLE-CODE").text),
                                 text=et_element.find("TEXT").text,
                                 display_trouble_code=display_trouble_code,
                                 level=level)


def read_data_object_property_from_odx(et_element):
    """Reads a DATA-OBJECT-PROP or a DTC-DOP."""
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME").text
    description = et_element.find("DESCRIPTION").text if et_element.find(
        "DESCRIPTION") is not None else None
    logger.debug('Parsing DOP ' + short_name)

    diag_coded_type = read_diag_coded_type_from_odx(
        et_element.find("DIAG-CODED-TYPE"))
    physical_data_type = et_element.find(
        "PHYSICAL-TYPE").get("BASE-DATA-TYPE")
    compu_method = read_compu_method_from_odx(et_element.find(
        "COMPU-METHOD"), diag_coded_type.base_data_type, physical_data_type)

    if et_element.tag == "DATA-OBJECT-PROP":
        dop = DataObjectProperty(id,
                                 short_name,
                                 diag_coded_type,
                                 physical_data_type,
                                 compu_method,
                                 long_name=long_name,
                                 description=description)
    else:
        # TODO
        dtcs = [read_dtc_from_odx(el)
                for el in et_element.iterfind("DTCS/DTC")]
        dtcs += [DtcRef(et_element.get("ID"))
                 for el in et_element.iterfind("DTCS/DTC-REF")]

        is_visible = et_element.get("IS-VISIBLE") == "true"
        dop = DtcDop(id,
                     short_name,
                     diag_coded_type,
                     physical_data_type,
                     compu_method,
                     dtcs,
                     is_visible=is_visible,
                     long_name=long_name,
                     description=description)
    return dop
