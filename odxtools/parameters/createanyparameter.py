# SPDX-License-Identifier: MIT
from typing import List
from xml.etree import ElementTree

from ..createanydiagcodedtype import create_any_diag_coded_type_from_et
from ..createsdgs import create_sdgs_from_et
from ..element import NamedElement
from ..exceptions import odxrequire
from ..globals import xsi
from ..odxlink import OdxDocFragment, OdxLinkId, OdxLinkRef
from ..utils import dataclass_fields_asdict
from .codedconstparameter import CodedConstParameter
from .dynamicparameter import DynamicParameter
from .lengthkeyparameter import LengthKeyParameter
from .matchingrequestparameter import MatchingRequestParameter
from .nrcconstparameter import NrcConstParameter
from .parameter import Parameter
from .physicalconstantparameter import PhysicalConstantParameter
from .reservedparameter import ReservedParameter
from .systemparameter import SystemParameter
from .tableentryparameter import TableEntryParameter
from .tablekeyparameter import TableKeyParameter
from .tablestructparameter import TableStructParameter
from .valueparameter import ValueParameter


def create_any_parameter_from_et(et_element: ElementTree.Element,
                                 doc_frags: List[OdxDocFragment]) \
                                 -> Parameter:
    kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, doc_frags))
    semantic = et_element.get("SEMANTIC")
    byte_position_str = et_element.findtext("BYTE-POSITION")
    byte_position = int(byte_position_str) if byte_position_str is not None else None
    bit_position_str = et_element.findtext("BIT-POSITION")
    bit_position = None
    if bit_position_str is not None:
        bit_position = int(bit_position_str)
    parameter_type = et_element.get(f"{xsi}type")

    sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

    # Which attributes are set depends on the type of the parameter.
    if parameter_type in ["VALUE", "PHYS-CONST", "SYSTEM", "LENGTH-KEY"]:
        dop_ref = OdxLinkRef.from_et(et_element.find("DOP-REF"), doc_frags)
        dop_snref = None
        if (dop_snref_elem := et_element.find("DOP-SNREF")) is not None:
            dop_snref = odxrequire(dop_snref_elem.get("SHORT-NAME"))

        if dop_ref is None and dop_snref is None:
            raise ValueError(
                f"A parameter of type {parameter_type} must reference a DOP! {dop_ref}, {dop_snref}"
            )

    if parameter_type == "VALUE":
        physical_default_value_raw = (
            et_element.findtext("PHYSICAL-DEFAULT-VALUE")
            if et_element.find("PHYSICAL-DEFAULT-VALUE") is not None else None)

        return ValueParameter(
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            physical_default_value_raw=physical_default_value_raw,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "PHYS-CONST":
        physical_constant_value = odxrequire(et_element.findtext("PHYS-CONSTANT-VALUE"))

        return PhysicalConstantParameter(
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            physical_constant_value_raw=physical_constant_value,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "CODED-CONST":
        dct_elem = odxrequire(et_element.find("DIAG-CODED-TYPE"))
        diag_coded_type = create_any_diag_coded_type_from_et(dct_elem, doc_frags)
        coded_value = diag_coded_type.base_data_type.from_string(
            odxrequire(et_element.findtext("CODED-VALUE")))

        return CodedConstParameter(
            semantic=semantic,
            diag_coded_type=diag_coded_type,
            coded_value=coded_value,
            byte_position=byte_position,
            bit_position=bit_position,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "NRC-CONST":
        diag_coded_type = create_any_diag_coded_type_from_et(
            odxrequire(et_element.find("DIAG-CODED-TYPE")), doc_frags)
        coded_values = [
            diag_coded_type.base_data_type.from_string(odxrequire(val.text))
            for val in et_element.iterfind("CODED-VALUES/CODED-VALUE")
        ]

        return NrcConstParameter(
            semantic=semantic,
            diag_coded_type=diag_coded_type,
            coded_values=coded_values,
            byte_position=byte_position,
            bit_position=bit_position,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "RESERVED":
        bit_length = int(odxrequire(et_element.findtext("BIT-LENGTH")))

        return ReservedParameter(
            bit_length=bit_length,
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "MATCHING-REQUEST-PARAM":
        byte_length = int(odxrequire(et_element.findtext("BYTE-LENGTH")))
        request_byte_pos = int(odxrequire(et_element.findtext("REQUEST-BYTE-POS")))

        return MatchingRequestParameter(
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            request_byte_position=request_byte_pos,
            byte_length=byte_length,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "SYSTEM":
        sysparam = odxrequire(et_element.get("SYSPARAM"))

        return SystemParameter(
            sysparam=sysparam,
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "LENGTH-KEY":
        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))

        return LengthKeyParameter(
            odx_id=odx_id,
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "DYNAMIC":

        return DynamicParameter(
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "TABLE-STRUCT":
        key_ref = OdxLinkRef.from_et(et_element.find("TABLE-KEY-REF"), doc_frags)
        if (key_snref_elem := et_element.find("TABLE-KEY-SNREF")) is not None:
            key_snref = odxrequire(key_snref_elem.get("SHORT-NAME"))
        else:
            key_snref = None

        return TableStructParameter(
            table_key_ref=key_ref,
            table_key_snref=key_snref,
            semantic=semantic,
            byte_position=byte_position,
            bit_position=bit_position,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "TABLE-KEY":

        parameter_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
        table_ref = OdxLinkRef.from_et(et_element.find("TABLE-REF"), doc_frags)
        if (table_snref_elem := et_element.find("TABLE-SNREF")) is not None:
            table_snref = odxrequire(table_snref_elem.get("SHORT-NAME"))
        else:
            table_snref = None

        table_row_ref = OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), doc_frags)
        if (table_row_snref_elem := et_element.find("TABLE-ROW-SNREF")) is not None:
            table_row_snref = odxrequire(table_row_snref_elem.get("SHORT-NAME"))
        else:
            table_row_snref = None

        return TableKeyParameter(
            table_ref=table_ref,
            table_snref=table_snref,
            table_row_snref=table_row_snref,
            table_row_ref=table_row_ref,
            odx_id=parameter_id,
            byte_position=byte_position,
            bit_position=bit_position,
            semantic=semantic,
            sdgs=sdgs,
            **kwargs)

    elif parameter_type == "TABLE-ENTRY":
        target = odxrequire(et_element.findtext("TARGET"))
        table_row_ref = odxrequire(OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), doc_frags))

        return TableEntryParameter(
            target=target,
            table_row_ref=table_row_ref,
            byte_position=byte_position,
            bit_position=bit_position,
            semantic=semantic,
            sdgs=sdgs,
            **kwargs)

    raise NotImplementedError(f"I don't know about parameters of type {parameter_type}")
