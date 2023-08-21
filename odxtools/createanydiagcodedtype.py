# SPDX-License-Identifier: MIT
from typing import List, cast
from xml.etree import ElementTree

from .diagcodedtype import DiagCodedType
from .exceptions import odxraise, odxrequire
from .globals import xsi
from .leadinglengthinfotype import LeadingLengthInfoType
from .minmaxlengthtype import MinMaxLengthType
from .odxlink import OdxDocFragment, OdxLinkRef
from .odxtypes import DataType, odxstr_to_bool
from .paramlengthinfotype import ParamLengthInfoType
from .standardlengthtype import StandardLengthType


def create_any_diag_coded_type_from_et(et_element: ElementTree.Element,
                                       doc_frags: List[OdxDocFragment]) -> DiagCodedType:
    base_type_encoding = et_element.get("BASE-TYPE-ENCODING")

    base_data_type_str = odxrequire(et_element.get("BASE-DATA-TYPE"))
    try:
        base_data_type = DataType(base_data_type_str)
    except ValueError:
        base_data_type = cast(DataType, None)
        odxraise(f"Unknown base data type {base_data_type_str}")

    is_highlow_byte_order_raw = odxstr_to_bool(et_element.get("IS-HIGHLOW-BYTE-ORDER"))

    dct_type = et_element.get(f"{xsi}type")
    bit_length = None
    if dct_type == "LEADING-LENGTH-INFO-TYPE":
        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))
        return LeadingLengthInfoType(
            base_data_type=base_data_type,
            bit_length=bit_length,
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw,
        )
    elif dct_type == "MIN-MAX-LENGTH-TYPE":
        min_length = int(odxrequire(et_element.findtext("MIN-LENGTH")))
        max_length = None
        if et_element.find("MAX-LENGTH") is not None:
            max_length = int(odxrequire(et_element.findtext("MAX-LENGTH")))
        termination = odxrequire(et_element.get("TERMINATION"))

        return MinMaxLengthType(
            base_data_type=base_data_type,
            min_length=min_length,
            max_length=max_length,
            termination=termination,
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw,
        )
    elif dct_type == "PARAM-LENGTH-INFO-TYPE":
        length_key_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("LENGTH-KEY-REF"), doc_frags))

        return ParamLengthInfoType(
            base_data_type=base_data_type,
            length_key_ref=length_key_ref,
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw,
        )
    elif dct_type == "STANDARD-LENGTH-TYPE":
        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))
        bit_mask = None
        if (bit_mask_str := et_element.findtext("BIT-MASK")) is not None:
            # The XSD uses the type xsd:hexBinary
            # xsd:hexBinary allows for leading/trailing whitespace, empty strings, and it only allows an even
            # number of hex digits, while some of the examples shown in the  ODX specification exhibit an
            # odd number of hex digits.
            # This causes a validation paradox, so we try to be flexible
            bit_mask_str = bit_mask_str.strip()
            if len(bit_mask_str):
                bit_mask = int(bit_mask_str, 16)
        is_condensed_raw = odxstr_to_bool(et_element.get("CONDENSED"))
        return StandardLengthType(
            base_data_type=base_data_type,
            bit_length=bit_length,
            bit_mask=bit_mask,
            is_condensed_raw=is_condensed_raw,
            base_type_encoding=base_type_encoding,
            is_highlow_byte_order_raw=is_highlow_byte_order_raw,
        )
    raise NotImplementedError(f"I do not know the diag-coded-type {dct_type}")
