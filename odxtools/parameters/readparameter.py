# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import List

from ..diagcodedtypes import read_diag_coded_type_from_odx
from ..globals import xsi
from ..utils import read_description_from_odx
from ..odxlink import OdxLinkRef, OdxLinkId, OdxDocFragment

from .codedconstparameter import CodedConstParameter
from .dynamicparameter import DynamicParameter
from .lengthkeyparameter import LengthKeyParameter
from .matchingrequestparameter import MatchingRequestParameter
from .nrcconstparameter import NrcConstParameter
from .physicalconstantparameter import PhysicalConstantParameter
from .reservedparameter import ReservedParameter
from .systemparameter import SystemParameter
from .tableentryparameter import TableEntryParameter
from .tablekeyparameter import TableKeyParameter
from .tablestructparameter import TableStructParameter
from .valueparameter import ValueParameter


def read_parameter_from_odx(et_element, doc_frags):
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    semantic = et_element.get("SEMANTIC")
    byte_position_str = et_element.findtext("BYTE-POSITION")
    byte_position = int(byte_position_str) if byte_position_str is not None else None
    bit_position_str = et_element.findtext("BIT-POSITION")
    bit_position = None
    if bit_position_str is not None:
        bit_position = int(bit_position_str)
    parameter_type = et_element.get(f"{xsi}type")

    # Which attributes are set depends on the type of the parameter.
    if parameter_type in ["VALUE", "PHYS-CONST", "SYSTEM", "LENGTH-KEY"]:
        dop_ref = OdxLinkRef.from_et(et_element.find("DOP-REF"), doc_frags)
        dop_snref = et_element.find(
            "DOP-SNREF").get("SHORT-NAME") if et_element.find("DOP-SNREF") is not None else None

        if dop_ref is None and dop_snref is None:
            raise ValueError(
                f"A parameter of type {parameter_type} must reference a DOP! {dop_ref}, {dop_snref}")

    if parameter_type == "VALUE":
        physical_default_value = et_element.find("PHYSICAL-DEFAULT-VALUE").text \
            if et_element.find("PHYSICAL-DEFAULT-VALUE") is not None else None

        return ValueParameter(short_name=short_name,
                              long_name=long_name,
                              semantic=semantic,
                              byte_position=byte_position,
                              bit_position=bit_position,
                              dop_ref=dop_ref,
                              dop_snref=dop_snref,
                              physical_default_value=physical_default_value,
                              description=description)

    elif parameter_type == "PHYS-CONST":
        physical_constant_value = et_element.find(
            "PHYS-CONSTANT-VALUE").text

        return PhysicalConstantParameter(short_name,
                                         long_name=long_name,
                                         semantic=semantic,
                                         byte_position=byte_position,
                                         bit_position=bit_position,
                                         dop_ref=dop_ref,
                                         dop_snref=dop_snref,
                                         physical_constant_value=physical_constant_value,
                                         description=description)

    elif parameter_type == "CODED-CONST":
        diag_coded_type = read_diag_coded_type_from_odx(
            et_element.find("DIAG-CODED-TYPE"), doc_frags)
        coded_value = diag_coded_type.base_data_type.from_string(
            et_element.find("CODED-VALUE").text)

        return CodedConstParameter(short_name,
                                   long_name=long_name,
                                   semantic=semantic,
                                   diag_coded_type=diag_coded_type,
                                   coded_value=coded_value,
                                   byte_position=byte_position,
                                   bit_position=bit_position,
                                   description=description)

    elif parameter_type == "NRC-CONST":
        diag_coded_type = read_diag_coded_type_from_odx(
            et_element.find("DIAG-CODED-TYPE"), doc_frags)
        coded_values = [diag_coded_type.base_data_type.from_string(val.text)
                        for val in et_element.iterfind("CODED-VALUES/CODED-VALUE")]

        return NrcConstParameter(short_name,
                                 long_name=long_name,
                                 semantic=semantic,
                                 diag_coded_type=diag_coded_type,
                                 coded_values=coded_values,
                                 byte_position=byte_position,
                                 bit_position=bit_position,
                                 description=description)

    elif parameter_type == "RESERVED":
        bit_length = int(et_element.find("BIT-LENGTH").text)

        return ReservedParameter(short_name,
                                 long_name=long_name,
                                 semantic=semantic,
                                 byte_position=byte_position,
                                 bit_position=bit_position,
                                 bit_length=bit_length,
                                 description=description)

    elif parameter_type == "MATCHING-REQUEST-PARAM":
        byte_length = int(et_element.find("BYTE-LENGTH").text)
        request_byte_pos = int(
            et_element.find("REQUEST-BYTE-POS").text)

        return MatchingRequestParameter(short_name,
                                        long_name=long_name,
                                        semantic=semantic,
                                        byte_position=byte_position, bit_position=bit_position,
                                        request_byte_position=request_byte_pos, byte_length=byte_length,
                                        description=description)

    elif parameter_type == "SYSTEM":
        sysparam = et_element.get("SYSPARAM")

        return SystemParameter(short_name=short_name,
                               sysparam=sysparam,
                               long_name=long_name,
                               semantic=semantic,
                               byte_position=byte_position,
                               bit_position=bit_position,
                               dop_ref=dop_ref,
                               dop_snref=dop_snref,
                               description=description)

    elif parameter_type == "LENGTH-KEY":
        odx_id = OdxLinkId.from_et(et_element, doc_frags)

        return LengthKeyParameter(short_name=short_name,
                                  odx_id=odx_id,
                                  long_name=long_name,
                                  semantic=semantic,
                                  byte_position=byte_position,
                                  bit_position=bit_position,
                                  dop_ref=dop_ref,
                                  dop_snref=dop_snref,
                                  description=description)

    elif parameter_type == "DYNAMIC":

        return DynamicParameter(short_name=short_name,
                                long_name=long_name,
                                semantic=semantic,
                                byte_position=byte_position,
                                bit_position=bit_position,
                                description=description)

    elif parameter_type == "TABLE-STRUCT":
        key_ref = OdxLinkRef.from_et(et_element.find("TABLE-KEY-REF"), doc_frags)
        key_snref = et_element.find(
            "TABLE-KEY-SNREF").get("SHORT-NAME") if et_element.find("TABLE-KEY-SNREF") is not None else None

        return TableStructParameter(short_name=short_name,
                                    table_key_ref=key_ref,
                                    table_key_snref=key_snref,
                                    long_name=long_name,
                                    semantic=semantic,
                                    byte_position=byte_position,
                                    bit_position=bit_position,
                                    description=description)

    elif parameter_type == "TABLE-KEY":

        parameter_id = OdxLinkId.from_et(et_element, doc_frags)
        table_ref = OdxLinkRef.from_et(et_element.find("TABLE-REF"), doc_frags)
        table_snref = et_element.find(
            "TABLE-SNREF").get("SHORT-NAME") if et_element.find("TABLE-SNREF") is not None else None
        row_snref = et_element.find(
            "TABLE-ROW-SNREF").get("SHORT-NAME") if et_element.find("TABLE-ROW-SNREF") is not None else None
        row_ref = OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), doc_frags)

        return TableKeyParameter(short_name=short_name,
                                 table_ref=table_ref,
                                 table_snref=table_snref,
                                 table_row_snref=row_snref,
                                 table_row_ref=row_ref,
                                 odx_id=parameter_id,
                                 long_name=long_name,
                                 byte_position=byte_position,
                                 bit_position=bit_position,
                                 semantic=semantic,
                                 description=description)

    elif parameter_type == "TABLE-ENTRY":
        target = et_element.find("TARGET").text
        table_row_ref = OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), doc_frags)

        return TableEntryParameter(short_name=short_name,
                                   target=target,
                                   table_row_ref=table_row_ref,
                                   long_name=long_name,
                                   byte_position=byte_position,
                                   bit_position=bit_position,
                                   semantic=semantic,
                                   description=description)

    raise NotImplementedError(f"I don't know the type {parameter_type}")
