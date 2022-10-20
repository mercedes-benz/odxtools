# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import Any, Dict, List, Optional, Union, Type

from ..odxtypes import DataType
from ..utils import read_description_from_odx
from ..globals import logger
from ..odxlink import OdxDocFragment

from .compumethodbase import CompuMethod
from .compuscale import CompuScale
from .identicalcompumethod import IdenticalCompuMethod
from .limit import IntervalType, Limit
from .linearcompumethod import LinearCompuMethod
from .scalelinearcompumethod import ScaleLinearCompuMethod
from .tabintpcompumethod import TabIntpCompuMethod
from .texttablecompumethod import TexttableCompuMethod


def _parse_compu_scale_to_linear_compu_method(scale_element,
                                              internal_type: DataType,
                                              physical_type: DataType,
                                              is_scale_linear=False,
                                              additional_kwargs={}):
    assert physical_type in [DataType.A_FLOAT32,
                             DataType.A_FLOAT64,
                             DataType.A_INT32,
                             DataType.A_UINT32]
    assert internal_type in [DataType.A_FLOAT32,
                             DataType.A_FLOAT64,
                             DataType.A_INT32,
                             DataType.A_UINT32]

    if physical_type.as_python_type() == float:
        computation_python_type = physical_type.from_string
    else:
        computation_python_type = internal_type.from_string

    kwargs = additional_kwargs.copy()
    kwargs["internal_type"] = internal_type
    kwargs["physical_type"] = physical_type

    coeffs = scale_element.find("COMPU-RATIONAL-COEFFS")
    nums = coeffs.iterfind("COMPU-NUMERATOR/V")

    offset = computation_python_type(next(nums).text)
    factor_el = next(nums, None)
    factor = computation_python_type(factor_el.text if factor_el is not None else '0')
    if coeffs.find("COMPU-DENOMINATOR/V") is not None:
        kwargs["denominator"] = float(
            coeffs.find("COMPU-DENOMINATOR/V").text)
        assert kwargs["denominator"] > 0

    # Read lower limit
    internal_lower_limit = read_limit_from_odx(
        scale_element.find("LOWER-LIMIT"),
        internal_type=internal_type
    )
    if internal_lower_limit is None:
        internal_lower_limit = Limit(float("-inf"), IntervalType.INFINITE)
    kwargs["internal_lower_limit"] = internal_lower_limit

    # Read upper limit
    internal_upper_limit = read_limit_from_odx(
        scale_element.find("UPPER-LIMIT"),
        internal_type=internal_type
    )
    if internal_upper_limit is None:
        if not is_scale_linear:
            internal_upper_limit = Limit(float("inf"), IntervalType.INFINITE)
        else:
            assert (internal_lower_limit is not None
                    and internal_lower_limit.interval_type == IntervalType.CLOSED)
            logger.info("Scale linear without UPPER-LIMIT")
            internal_upper_limit = internal_lower_limit
    kwargs["internal_upper_limit"] = internal_upper_limit

    return LinearCompuMethod(offset=offset, factor=factor, **kwargs)


def read_limit_from_odx(et_element, internal_type: DataType):
    limit: Optional[Limit] = None
    if et_element is not None:
        if et_element.get("INTERVAL-TYPE"):
            interval_type = IntervalType(et_element.get("INTERVAL-TYPE"))
        else:
            interval_type = IntervalType.CLOSED

        if interval_type == IntervalType.INFINITE:
            if et_element.tag == "LOWER-LIMIT":
                limit = Limit(float("-inf"), interval_type)
            else:
                assert et_element.tag == "UPPER-LIMIT"
                limit = Limit(float("inf"), interval_type)
        else:
            if internal_type == DataType.A_BYTEFIELD:
                hex_text = et_element.text
                if len(hex_text) % 2 == 1:
                    hex_text = '0' + hex_text
                limit = Limit(bytearray.fromhex(hex_text), interval_type)
            else:
                limit = Limit(internal_type.from_string(et_element.text),
                              interval_type)
    return limit


def read_compu_method_from_odx(et_element,
                               doc_frags: List[OdxDocFragment],
                               internal_type: DataType,
                               physical_type: DataType) -> CompuMethod:
    compu_category = et_element.find("CATEGORY").text
    assert compu_category in ["IDENTICAL", "LINEAR", "SCALE-LINEAR",
                              "TEXTTABLE", "COMPUCODE", "TAB-INTP",
                              "RAT-FUNC", "SCALE-RAT-FUNC"]

    if et_element.find("COMPU-PHYS-TO-INTERNAL") is not None:  # TODO: Is this never used?
        raise NotImplementedError(
            f"Found COMPU-PHYS-TO-INTERNAL for category {compu_category}")

    kwargs: Dict[str, Any] = {"internal_type": internal_type}

    if compu_category == "IDENTICAL":
        assert (internal_type == physical_type or (
            internal_type in [DataType.A_ASCIISTRING,  DataType.A_UTF8STRING] and physical_type == DataType.A_UNICODE2STRING)
        ), (f"Internal type '{internal_type}' and physical type '{physical_type}'"
            f" must be the same for compu methods of category '{compu_category}'")
        return IdenticalCompuMethod(internal_type=internal_type, physical_type=physical_type)

    if compu_category == "TEXTTABLE":
        assert physical_type == DataType.A_UNICODE2STRING
        compu_internal_to_phys = et_element.find("COMPU-INTERNAL-TO-PHYS")

        internal_to_phys: List[CompuScale] = []
        for scale in compu_internal_to_phys.iterfind("COMPU-SCALES/COMPU-SCALE"):
            lower_limit = read_limit_from_odx(scale.find("LOWER-LIMIT"),
                                              internal_type=internal_type)
            upper_limit = read_limit_from_odx(scale.find("UPPER-LIMIT"),
                                              internal_type=internal_type)

            if (vt := scale.find("COMPU-INVERSE-VALUE/VT")) is not None:
                compu_inverse_value = internal_type.from_string(vt.text)
            elif (v := scale.find("COMPU-INVERSE-VALUE/V")) is not None:
                compu_inverse_value = internal_type.from_string(v.text)
            else:
                compu_inverse_value = None

            internal_to_phys.append(CompuScale(
                short_label=(scale.find("SHORT-LABEL").text
                             if scale.find("SHORT-LABEL") is not None else None),
                description=read_description_from_odx(scale.find("DESC")),
                lower_limit=lower_limit,
                upper_limit=upper_limit,
                compu_inverse_value=compu_inverse_value,
                compu_const=scale.find("COMPU-CONST").find("VT").text
            ))

        kwargs["internal_to_phys"] = internal_to_phys
        return TexttableCompuMethod(**kwargs)

    elif compu_category == "LINEAR":
        # Compu method can be described by the function f(x) = (offset + factor * x) / denominator

        scale = et_element.find(
            "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
        return _parse_compu_scale_to_linear_compu_method(scale, internal_type, physical_type, additional_kwargs=kwargs)

    elif compu_category == "SCALE-LINEAR":

        scales = et_element.iterfind(
            "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
        linear_methods = [_parse_compu_scale_to_linear_compu_method(
            scale, internal_type, physical_type, additional_kwargs=kwargs) for scale in scales]
        return ScaleLinearCompuMethod(linear_methods)

    elif compu_category == "TAB-INTP":

        scales = et_element.findall(
            "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
        internal = [scale.findtext("LOWER-LIMIT") for scale in scales]
        physical = [scale.findtext("COMPU-CONST/V") for scale in scales]

        internal = [internal_type.from_string(x) for x in internal]
        physical = [physical_type.from_string(x) for x in physical]

        return TabIntpCompuMethod(internal_type=internal_type, physical_type=physical_type, internal_points=internal, physical_points=physical)

    # TODO: Implement other categories (never instantiate CompuMethod)
    logger.warning(
        f"Warning: Computation category {compu_category} is not implemented!")
    return CompuMethod(DataType.A_UINT32, DataType.A_UINT32, f"NOT-IMPLEMENTED:{compu_category}")
