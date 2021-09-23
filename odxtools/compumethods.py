# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import abc
from odxtools.exceptions import DecodeError

from typing import Iterable

from .globals import logger
from .odxtypes import ODX_TYPE_TO_PYTHON_TYPE, ODX_TYPE_PARSER, _odx_isinstance


class CompuMethod:
    def __init__(self):
        pass

    @property
    @abc.abstractclassmethod
    def category(self) -> str:
        """ODX type of the compu method, e.g. TEXTTABLE, IDENTITCAL, SCALE-LINEAR"""
        raise NotImplementedError()

    @abc.abstractclassmethod
    def convert_physical_to_internal(self, physical_value):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def convert_internal_to_physical(self, internal_value):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def is_valid_physical_value(self, physical_value):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def is_valid_internal_value(self, internal_value):
        raise NotImplementedError()

    def get_valid_physical_values(self):
        return None


class IdenticalCompuMethod(CompuMethod):
    def __init__(self, internal_type, physical_type):
        self.internal_type = internal_type
        self.physical_type = physical_type

    @property
    def category(self):
        return "IDENTICAL"

    def convert_physical_to_internal(self, physical_value):
        return physical_value

    def convert_internal_to_physical(self, internal_value):
        return internal_value

    def is_valid_physical_value(self, physical_value):
        return _odx_isinstance(physical_value, self.physical_type)

    def is_valid_internal_value(self, internal_value):
        return _odx_isinstance(internal_value, self.internal_type)


class TexttableCompuMethod(CompuMethod):
    def __init__(self, internal_to_phys, internal_type):
        self.internal_type = internal_type
        self.physical_type = "A_UNICODE2STRING"
        self.internal_to_phys = internal_to_phys

        assert all(scale["LOWER-LIMIT"] is not None or scale["UPPER-LIMIT"]
                   is not None for scale in self.internal_to_phys), "Text table compu method doesn't have expected format!"

    @property
    def category(self):
        return "TEXTTABLE"

    def convert_physical_to_internal(self, physical_value):
        scale = next(filter(
            lambda scale: scale["COMPU-CONST"] == physical_value, self.internal_to_phys), None)
        if scale is not None:
            res = scale["COMPU-INVERSE-VALUE"] if scale["COMPU-INVERSE-VALUE"] is not None else scale["LOWER-LIMIT"]
            assert isinstance(res, int)
            return res

    def __is_internal_in_scale(self, internal_value, scale):
        if scale["UPPER-LIMIT"] is None:
            return internal_value == scale["LOWER-LIMIT"]
        else:
            return scale["LOWER-LIMIT"] <= internal_value and internal_value <= scale["UPPER-LIMIT"]

    def convert_internal_to_physical(self, internal_value):
        try:
            scale = next(filter(lambda scale: self.__is_internal_in_scale(internal_value, scale),
                                self.internal_to_phys))
        except StopIteration:
            raise DecodeError(
                f"Texttable compu method could not decode {internal_value} to string.")
        return scale["COMPU-CONST"]

    def is_valid_physical_value(self, physical_value):
        return physical_value in map(lambda x: x["COMPU-CONST"], self.internal_to_phys)

    def is_valid_internal_value(self, internal_value):
        return any(self.__is_internal_in_scale(internal_value, scale) for scale in self.internal_to_phys)

    def get_valid_physical_values(self):
        return list(map(lambda x: x["COMPU-CONST"], self.internal_to_phys))


class LinearCompuMethod(CompuMethod):
    """Represents the decoding function f(x) = (offset + factor * x) / denominator
    where f(x) is the physical value and x is the internal value.
    """

    def __init__(self,
                 offset,
                 factor,
                 internal_type,
                 physical_type,
                 denominator=1,
                 internal_lower_limit=None,
                 internal_upper_limit=None,
                 lower_interval_type=None,
                 upper_interval_type=None):
        self.offset = offset
        self.factor = factor
        self.denominator = denominator
        self.internal_type = internal_type
        self.physical_type = physical_type

        if lower_interval_type is not None:
            self.lower_interval_type = lower_interval_type
        elif internal_lower_limit is None or internal_lower_limit == float("-inf"):
            self.lower_interval_type = "INFINITE"
        else:
            self.lower_interval_type = "CLOSED"

        if upper_interval_type is not None:
            self.upper_interval_type = upper_interval_type
        elif internal_upper_limit is None or internal_upper_limit == float("inf"):
            self.upper_interval_type = "INFINITE"
        else:
            self.upper_interval_type = "CLOSED"

        self.internal_lower_limit = internal_lower_limit if self.lower_interval_type != "INFINITE" else float(
            "-inf")
        self.internal_upper_limit = internal_upper_limit if self.upper_interval_type != "INFINITE" else float(
            "inf")
        assert self.internal_lower_limit is not None and self.internal_upper_limit is not None
        assert denominator > 0 and type(denominator) == int

    @property
    def category(self):
        return "LINEAR"

    def convert_internal_to_physical(self, internal_value):
        assert self.is_valid_internal_value(internal_value) or internal_value in [
            self.internal_lower_limit, self.internal_upper_limit]
        if self.denominator is None:
            result = self.offset + self.factor * internal_value
        else:
            result = (self.offset + self.factor *
                      internal_value) / self.denominator

        if self.internal_type == "A_FLOAT64" and self.physical_type in ["A_INT32", "A_UINT32"]:
            result = round(result)
        return ODX_TYPE_PARSER[self.physical_type](result)

    def convert_physical_to_internal(self, physical_value):
        assert self.is_valid_physical_value(
            physical_value), f"physical value {physical_value} of type {type(physical_value)} is not valid. Expected type {self.physical_type} with internal range {self.internal_lower_limit} to {self.internal_upper_limit}"
        if self.denominator is None:
            result = (physical_value - self.offset) / self.factor
        else:
            result = ((physical_value * self.denominator) -
                      self.offset) / self.factor

        if self.physical_type == "A_FLOAT64" and self.internal_type in ["A_INT32", "A_UINT32"]:
            result = round(result)
        return ODX_TYPE_PARSER[self.internal_type](result)

    def is_valid_physical_value(self, physical_value):
        # Do type checks
        expected_type = ODX_TYPE_TO_PYTHON_TYPE[self.physical_type]
        if expected_type == float and type(physical_value) not in [int, float]:
            return False
        elif expected_type != float and type(physical_value) != expected_type:
            return False

        # If conversion changes sign (i.e. swaps lower and upper limit) swap them back here for comparison
        invert = -1 if self.factor < 0 else 1
        physical_value *= invert

        if self.lower_interval_type != "INFINITE":
            physical_lower_limit = self.convert_internal_to_physical(
                self.internal_lower_limit) * invert
            if self.lower_interval_type == "CLOSED" and physical_lower_limit > physical_value:
                return False
            elif self.lower_interval_type == "OPEN" and physical_lower_limit >= physical_value:
                return False
        if self.upper_interval_type != "INFINITE":
            physical_upper_limit = self.convert_internal_to_physical(
                self.internal_upper_limit) * invert
            if self.upper_interval_type == "CLOSED" and physical_upper_limit < physical_value:
                return False
            elif self.upper_interval_type == "OPEN" and physical_upper_limit <= physical_value:
                return False

        return True

    def is_valid_internal_value(self, internal_value):
        expected_type = ODX_TYPE_TO_PYTHON_TYPE[self.internal_type]
        if expected_type == float and type(internal_value) not in [int, float]:
            # logger.info(
            #    f"Internal: Type of {internal_value} is {type(internal_value)}, expected is {expected_type}")
            return False
        elif expected_type != float and type(internal_value) != expected_type:
            # logger.info(
            #    f"Internal: Type of {internal_value} is {type(internal_value)}, expected is {expected_type}")
            return False

        if self.lower_interval_type != "INFINITE":
            if self.lower_interval_type == "CLOSED" and self.internal_lower_limit > internal_value:
                return False
            elif self.lower_interval_type == "OPEN" and self.internal_lower_limit >= internal_value:
                return False
        if self.upper_interval_type != "INFINITE":
            if self.upper_interval_type == "CLOSED" and self.internal_upper_limit < internal_value:
                return False
            elif self.upper_interval_type == "OPEN" and self.internal_upper_limit <= internal_value:
                return False

        return True


class ScaleLinearCompuMethod(CompuMethod):
    def __init__(self, linear_methods: Iterable[LinearCompuMethod]):
        self.linear_methods = linear_methods
        logger.debug("Created scale linear compu method!")

    @property
    def category(self):
        return "SCALE-LINEAR"

    def convert_physical_to_internal(self, physical_value):
        assert self.is_valid_physical_value(
            physical_value), f"cannot convert the invalid physical value {physical_value} of type {type(physical_value)}"
        lin_method = next(
            scale for scale in self.linear_methods if scale.is_valid_physical_value(physical_value))
        return lin_method.convert_physical_to_internal(physical_value)

    def convert_internal_to_physical(self, internal_value):
        lin_method = next(
            scale for scale in self.linear_methods if scale.is_valid_internal_value(internal_value))
        return lin_method.convert_internal_to_physical(internal_value)

    def is_valid_physical_value(self, physical_value):
        return any(True for scale in self.linear_methods if scale.is_valid_physical_value(physical_value))

    def is_valid_internal_value(self, internal_value):
        return any(True for scale in self.linear_methods if scale.is_valid_internal_value(internal_value))


def _parse_compu_scale_to_linear_compu_method(scale_element, internal_type, physical_type, is_scale_linear=False, additional_kwargs={}):
    assert physical_type in ["A_FLOAT32", "A_FLOAT64", "A_INT32", "A_UINT32"]
    assert internal_type in ["A_FLOAT32", "A_FLOAT64", "A_INT32", "A_UINT32"]

    internal_python_type = float if internal_type.startswith(
        "A_FLOAT") else int

    if internal_type.startswith("A_FLOAT") or physical_type.startswith("A_FLOAT"):
        computation_python_type = float
    else:
        computation_python_type = int

    kwargs = additional_kwargs.copy()
    kwargs["internal_type"] = internal_type
    kwargs["physical_type"] = physical_type

    coeffs = scale_element.find("COMPU-RATIONAL-COEFFS")
    nums = coeffs.iterfind("COMPU-NUMERATOR/V")

    offset = computation_python_type(next(nums).text)
    factor = computation_python_type(next(nums).text)
    if coeffs.find("COMPU-DENOMINATOR/V") is not None:
        kwargs["denominator"] = int(
            coeffs.find("COMPU-DENOMINATOR/V").text)
        assert kwargs["denominator"] > 0

    if scale_element.find("LOWER-LIMIT") is not None:
        interval_type = scale_element.find("LOWER-LIMIT").get("INTERVAL-TYPE")
        if interval_type is not None:
            kwargs["lower_interval_type"] = interval_type

        if kwargs.get("lower_interval_type") == "INFINITE":
            kwargs["internal_lower_limit"] = float("-inf")
        elif scale_element.find("LOWER-LIMIT").text is not None:
            kwargs["internal_lower_limit"] = internal_python_type(
                scale_element.find("LOWER-LIMIT").text)
        else:
            raise NotImplementedError("Couldn't interpret lower limit!")

    if scale_element.find("UPPER-LIMIT") is not None:
        interval_type = scale_element.find("UPPER-LIMIT").get("INTERVAL-TYPE")
        if interval_type is not None:
            kwargs["upper_interval_type"] = interval_type

        if kwargs.get("upper_interval_type") == "INFINITE":
            kwargs["internal_upper_limit"] = float("inf")
        elif scale_element.find("UPPER-LIMIT").text is not None:
            kwargs["internal_upper_limit"] = internal_python_type(
                scale_element.find("UPPER-LIMIT").text)
        else:
            raise NotImplementedError("Couldn't interpret upper limit!")

    elif is_scale_linear:
        assert kwargs.get("internal_lower_limit") is not None and kwargs.get(
            "lower_interval_type") == "CLOSED"
        logger.info("Scale linear without UPPER-LIMIT")
        kwargs["internal_upper_limit"] = kwargs["internal_lower_limit"]
        kwargs["upper_interval_type"] = "CLOSED"

    return LinearCompuMethod(offset=offset, factor=factor, **kwargs)


def read_compu_method_from_odx(et_element, internal_type, physical_type) -> CompuMethod:
    compu_category = et_element.find("CATEGORY").text
    assert compu_category in ["IDENTICAL", "LINEAR", "SCALE-LINEAR",
                              "TEXTTABLE", "COMPUCODE", "TAB-INTP",
                              "RAT-FUNC", "SCALE-RAT-FUNC"]

    if et_element.find("COMPU-PHYS-TO-INTERNAL") is not None:  # TODO: Is this never used?
        raise NotImplementedError(
            f"Found COMPU-PHYS-TO-INTERNAL for category {compu_category}")

    kwargs = {"internal_type": internal_type}

    if compu_category == "IDENTICAL":
        assert internal_type == physical_type or (internal_type in ["A_ASCIISTRING",  "A_UTF8STRING"] and physical_type ==
                                                  "A_UNICODE2STRING"), f"Internal type '{internal_type}' and physical type '{physical_type}' must be the same for compu methods of category '{compu_category}'"
        return IdenticalCompuMethod(internal_type=internal_type, physical_type=physical_type)

    if compu_category == "TEXTTABLE":
        assert physical_type == "A_UNICODE2STRING"
        compu_internal_to_phys = et_element.find("COMPU-INTERNAL-TO-PHYS")

        if internal_type == "A_BYTEFIELD":
            internal_to_phys = [
                {
                    "COMPU-CONST": scale.find("COMPU-CONST").find("VT").text,
                    "LOWER-LIMIT": int("0x" + scale.find("LOWER-LIMIT").text, 16) if scale.find("LOWER-LIMIT") is not None else None,
                    "UPPER-LIMIT": int("0x" + scale.find("UPPER-LIMIT").text, 16) if scale.find("UPPER-LIMIT") is not None else None,
                    "COMPU-INVERSE-VALUE": scale.find("COMPU-INVERSE-VALUE/VT").text if scale.find("COMPU-INVERSE-VALUE/VT") is not None
                    else float(scale.find("COMPU-INVERSE-VALUE/V").text) if scale.find("COMPU-INVERSE-VALUE/V") is not None else None
                } for scale in compu_internal_to_phys.iterfind("COMPU-SCALES/COMPU-SCALE")
            ]
        else:
            internal_to_phys = [
                {
                    "COMPU-CONST": scale.find("COMPU-CONST").find("VT").text,
                    "LOWER-LIMIT": int(scale.find("LOWER-LIMIT").text) if scale.find("LOWER-LIMIT") is not None else None,
                    "UPPER-LIMIT": int(scale.find("UPPER-LIMIT").text) if scale.find("UPPER-LIMIT") is not None else None,
                    "COMPU-INVERSE-VALUE": scale.find("COMPU-INVERSE-VALUE/VT").text if scale.find("COMPU-INVERSE-VALUE/VT") is not None
                    else float(scale.find("COMPU-INVERSE-VALUE/V").text) if scale.find("COMPU-INVERSE-VALUE/V") is not None else None
                } for scale in compu_internal_to_phys.iterfind("COMPU-SCALES/COMPU-SCALE")
            ]
        kwargs["internal_to_phys"] = internal_to_phys
        assert all(isinstance(scale["LOWER-LIMIT"], int) or isinstance(scale["UPPER-LIMIT"], int)
                   for scale in internal_to_phys), "Text table compu method doesn't have expected format!"
        return TexttableCompuMethod(**kwargs)

    if compu_category == "LINEAR":
        # Compu method can be described by the function f(x) = (offset + factor * x) / denominator

        scale = et_element.find(
            "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
        return _parse_compu_scale_to_linear_compu_method(scale, internal_type, physical_type, additional_kwargs=kwargs)

    if compu_category == "SCALE-LINEAR":

        scales = et_element.iterfind(
            "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE")
        linear_methods = [_parse_compu_scale_to_linear_compu_method(
            scale, internal_type, physical_type, additional_kwargs=kwargs) for scale in scales]
        return ScaleLinearCompuMethod(linear_methods)

    # ToDo: Implement other categories (never instantiate CompuMethod)
    logger.warning(
        f"Warning: Computation category {compu_category} is not implemented!")
    return CompuMethod()
