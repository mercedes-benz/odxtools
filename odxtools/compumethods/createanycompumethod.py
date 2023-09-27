# SPDX-License-Identifier: MIT
import warnings
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from ..exceptions import OdxWarning, odxassert, odxraise, odxrequire
from ..globals import logger
from ..odxlink import OdxDocFragment
from ..odxtypes import DataType
from .compumethod import CompuMethod
from .compuscale import CompuScale
from .identicalcompumethod import IdenticalCompuMethod
from .limit import IntervalType, Limit
from .linearcompumethod import LinearCompuMethod
from .scalelinearcompumethod import ScaleLinearCompuMethod
from .tabintpcompumethod import TabIntpCompuMethod
from .texttablecompumethod import TexttableCompuMethod


def _parse_compu_scale_to_linear_compu_method(
    *,
    scale_element: ElementTree.Element,
    internal_type: DataType,
    physical_type: DataType,
    is_scale_linear: bool = False,
    **kwargs: Any,
) -> LinearCompuMethod:
    odxassert(physical_type in [
        DataType.A_FLOAT32,
        DataType.A_FLOAT64,
        DataType.A_INT32,
        DataType.A_UINT32,
    ])
    odxassert(internal_type in [
        DataType.A_FLOAT32,
        DataType.A_FLOAT64,
        DataType.A_INT32,
        DataType.A_UINT32,
    ])

    if physical_type.as_python_type() == float:
        computation_python_type = physical_type.from_string
    else:
        computation_python_type = internal_type.from_string

    kwargs = kwargs.copy()
    kwargs["internal_type"] = internal_type
    kwargs["physical_type"] = physical_type

    coeffs = odxrequire(scale_element.find("COMPU-RATIONAL-COEFFS"))
    nums = coeffs.iterfind("COMPU-NUMERATOR/V")

    offset = computation_python_type(odxrequire(next(nums).text))
    factor_el = next(nums, None)
    factor = computation_python_type(odxrequire(factor_el.text) if factor_el is not None else "0")
    denominator = 1.0
    if (string := coeffs.findtext("COMPU-DENOMINATOR/V")) is not None:
        denominator = float(string)
        if denominator == 0:
            warnings.warn(
                "CompuMethod: A denominator of zero will lead to divisions by zero.",
                OdxWarning,
                stacklevel=1)
    # Read lower limit
    internal_lower_limit = Limit.from_et(
        scale_element.find("LOWER-LIMIT"),
        internal_type=internal_type,
    )
    if internal_lower_limit is None:
        internal_lower_limit = Limit(0, IntervalType.INFINITE)
    kwargs["internal_lower_limit"] = internal_lower_limit

    # Read upper limit
    internal_upper_limit = Limit.from_et(
        scale_element.find("UPPER-LIMIT"),
        internal_type=internal_type,
    )
    if internal_upper_limit is None:
        if not is_scale_linear:
            internal_upper_limit = Limit(0, IntervalType.INFINITE)
        else:
            odxassert(internal_lower_limit is not None and
                      internal_lower_limit.interval_type == IntervalType.CLOSED)
            logger.info("Scale linear without UPPER-LIMIT")
            internal_upper_limit = internal_lower_limit
    kwargs["internal_upper_limit"] = internal_upper_limit
    kwargs["denominator"] = denominator
    kwargs["factor"] = factor
    kwargs["offset"] = offset

    return LinearCompuMethod(**kwargs)


def create_compu_default_value(et_element: Optional[ElementTree.Element],
                               doc_frags: List[OdxDocFragment], internal_type: DataType,
                               physical_type: DataType) -> Optional[CompuScale]:
    if et_element is None:
        return None
    compu_const = physical_type.create_from_et(et_element)
    scale = CompuScale.from_et(
        et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
    scale.compu_const = compu_const
    return scale


def create_any_compu_method_from_et(et_element: ElementTree.Element,
                                    doc_frags: List[OdxDocFragment], internal_type: DataType,
                                    physical_type: DataType) -> CompuMethod:
    compu_category = et_element.findtext("CATEGORY")
    odxassert(compu_category in [
        "IDENTICAL",
        "LINEAR",
        "SCALE-LINEAR",
        "TEXTTABLE",
        "COMPUCODE",
        "TAB-INTP",
        "RAT-FUNC",
        "SCALE-RAT-FUNC",
    ])

    if et_element.find("COMPU-PHYS-TO-INTERNAL") is not None:  # TODO: Is this never used?
        raise NotImplementedError(f"Found COMPU-PHYS-TO-INTERNAL for category {compu_category}")

    kwargs: Dict[str, Any] = {
        "physical_type": physical_type,
        "internal_type": internal_type,
    }

    if compu_category == "IDENTICAL":
        odxassert(
            internal_type == physical_type or
            (internal_type in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING] and
             physical_type == DataType.A_UNICODE2STRING),
            f"Internal type '{internal_type}' and physical type '{physical_type}'"
            f" must be the same for compu methods of category '{compu_category}'")
        return IdenticalCompuMethod(internal_type=internal_type, physical_type=physical_type)

    if compu_category == "TEXTTABLE":
        odxassert(physical_type == DataType.A_UNICODE2STRING)
        compu_internal_to_phys = odxrequire(et_element.find("COMPU-INTERNAL-TO-PHYS"))

        internal_to_phys: List[CompuScale] = []
        for scale_elem in compu_internal_to_phys.iterfind("COMPU-SCALES/COMPU-SCALE"):
            internal_to_phys.append(
                CompuScale.from_et(
                    scale_elem, doc_frags, internal_type=internal_type,
                    physical_type=physical_type))
        compu_default_value = create_compu_default_value(
            et_element.find("COMPU-DEFAULT-VALUE"), doc_frags, **kwargs)

        return TexttableCompuMethod(
            internal_to_phys=internal_to_phys,
            compu_default_value=compu_default_value,
            **kwargs,
        )

    elif compu_category == "LINEAR":
        # Compu method can be described by the function f(x) = (offset + factor * x) / denominator

        scale_elem = odxrequire(et_element.find("COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE"))
        return _parse_compu_scale_to_linear_compu_method(scale_element=scale_elem, **kwargs)

    elif compu_category == "SCALE-LINEAR":

        scale_elems = et_element.iterfind("COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
        linear_methods = [
            _parse_compu_scale_to_linear_compu_method(scale_element=scale_elem, **kwargs)
            for scale_elem in scale_elems
        ]
        return ScaleLinearCompuMethod(linear_methods=linear_methods, **kwargs)

    elif compu_category == "TAB-INTP":
        internal_points = []
        physical_points = []
        for scale_elem in et_element.iterfind("COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE"):
            internal_point = internal_type.from_string(
                odxrequire(scale_elem.findtext("LOWER-LIMIT")))
            physical_point = physical_type.create_from_et(
                odxrequire(scale_elem.find("COMPU-CONST")))

            if not isinstance(internal_point, (float, int)):
                odxraise()
            if not isinstance(physical_point, (float, int)):
                odxraise()

            internal_points.append(internal_point)
            physical_points.append(physical_point)

        return TabIntpCompuMethod(
            internal_points=internal_points, physical_points=physical_points, **kwargs)

    # TODO: Implement other categories (never instantiate CompuMethod)
    logger.warning(f"Warning: Computation category {compu_category} is not implemented!")
    return IdenticalCompuMethod(internal_type=DataType.A_UINT32, physical_type=DataType.A_UINT32)
