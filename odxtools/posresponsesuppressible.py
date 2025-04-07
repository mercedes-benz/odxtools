# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .utils import read_hex_binary


# note that the spec has a typo here: it calls the corresponding
# XML tag POS-RESPONSE-SUPPRESSABLE...
@dataclass(kw_only=True)
class PosResponseSuppressible:
    bit_mask: int

    coded_const_snref: str | None = None
    coded_const_snpathref: str | None = None

    value_snref: str | None = None
    value_snpathref: str | None = None

    phys_const_snref: str | None = None
    phys_const_snpathref: str | None = None

    table_key_snref: str | None = None
    table_key_snpathref: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "PosResponseSuppressible":

        bit_mask = odxrequire(read_hex_binary(et_element.find("BIT-MASK")))

        coded_const_snref = None
        if (cc_snref_elem := et_element.find("CODED-CONST-SNREF")) is not None:
            coded_const_snref = cc_snref_elem.attrib["SHORT-NAME"]
        coded_const_snpathref = None
        if (cc_snpathref_elem := et_element.find("CODED-CONST-SNPATHREF")) is not None:
            coded_const_snpathref = cc_snpathref_elem.attrib["SHORT-NAME-PATH"]

        value_snref = None
        if (cc_snref_elem := et_element.find("VALUE-SNREF")) is not None:
            value_snref = cc_snref_elem.attrib["SHORT-NAME"]
        value_snpathref = None
        if (cc_snpathref_elem := et_element.find("VALUE-SNPATHREF")) is not None:
            value_snpathref = cc_snpathref_elem.attrib["SHORT-NAME-PATH"]

        phys_const_snref = None
        if (cc_snref_elem := et_element.find("PHYS-CONST-SNREF")) is not None:
            phys_const_snref = cc_snref_elem.attrib["SHORT-NAME"]
        phys_const_snpathref = None
        if (cc_snpathref_elem := et_element.find("PHYS-CONST-SNPATHREF")) is not None:
            phys_const_snpathref = cc_snpathref_elem.attrib["SHORT-NAME-PATH"]

        table_key_snref = None
        if (cc_snref_elem := et_element.find("TABLE-KEY-SNREF")) is not None:
            table_key_snref = cc_snref_elem.attrib["SHORT-NAME"]
        table_key_snpathref = None
        if (cc_snpathref_elem := et_element.find("TABLE-KEY-SNPATHREF")) is not None:
            table_key_snpathref = cc_snpathref_elem.attrib["SHORT-NAME-PATH"]

        return PosResponseSuppressible(
            bit_mask=bit_mask,
            coded_const_snref=coded_const_snref,
            coded_const_snpathref=coded_const_snpathref,
            value_snref=value_snref,
            value_snpathref=value_snpathref,
            phys_const_snref=phys_const_snref,
            phys_const_snpathref=phys_const_snpathref,
            table_key_snref=table_key_snref,
            table_key_snpathref=table_key_snpathref,
        )
