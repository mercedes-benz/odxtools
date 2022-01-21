# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import abc

from typing import Iterable, List, NamedTuple, Optional, Union
from enum import Enum

from .utils import read_description_from_odx

from .exceptions import DecodeError
from .globals import logger
from .odxtypes import DataType


class CompuMethod:
    def __init__(self, internal_type: DataType, physical_type: DataType):
        self.internal_type = DataType(internal_type)
        self.physical_type = DataType(physical_type)

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
    @property
    def category(self):
        return "IDENTICAL"

    def convert_physical_to_internal(self, physical_value):
        return physical_value

    def convert_internal_to_physical(self, internal_value):
        return internal_value

    def is_valid_physical_value(self, physical_value):
        return self.physical_type.isinstance(physical_value)

    def is_valid_internal_value(self, internal_value):
        return self.internal_type.isinstance(internal_value)


class IntervalType(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    INFINITE = "INFINITE"


class Limit(NamedTuple):
    value: Union[str, int, bytes]
    interval_type: IntervalType = IntervalType.CLOSED

    def complies_to_upper(self, value):
        """Checks if the value is in the range w.r.t. the upper limit.

        * If the interval type is closed, return `value <= limit.value`.
        * If the interval type is open, return `value < limit.value`.
        * If the interval type is infinite, return `True`.
        """
        if self.interval_type == IntervalType.CLOSED:
            return value <= self.value
        elif self.interval_type == IntervalType.OPEN:
            return value < self.value
        elif self.interval_type == IntervalType.INFINITE:
            return True

    def complies_to_lower(self, value):
        """Checks if the value is in the range w.r.t. the lower limit.

        * If the interval type is closed, return `limit.value <= value`.
        * If the interval type is open, return `limit.value < value`.
        * If the interval type is infinite, return `True`.
        """
        if self.interval_type == IntervalType.CLOSED:
            return self.value <= value
        elif self.interval_type == IntervalType.OPEN:
            return self.value < value
        elif self.interval_type == IntervalType.INFINITE:
            return True


class CompuRationalCoeffs(NamedTuple):
    numerators: List[float]
    denominators: List[float] = None


class CompuScale(NamedTuple):
    """A COMPU-SCALE represents one value range of a COMPU-METHOD.

    Example:

    For a TEXTTABLE compu method a compu scale within COMPU-INTERNAL-TO-PHYS
    can be defined with
    ```
    scale = CompuScale(
        short_label="example_label", # optional: provide a label
        description="<p>fancy description</p>", # optional: provide a description
        lower_limit=Limit(0), # required: lower limit
        upper_limit=Limit(3), # required: upper limit
        compu_inverse_value=2, # required iff lower_limit != upper_limit
        compu_const="true", # required: physical value to be shown to the user
    )
    ```

    Almost all attributes are optional but there are compu-method-specific restrictions.
    E.g., lower_limit must always be defined unless the COMPU-METHOD is of CATEGORY LINEAR or RAT-FUNC.
    Either `compu_const` or `compu_rational_coeffs` must be defined but never both.
    """
    short_label: str = None
    description: str = None
    lower_limit: Limit = None
    upper_limit: Limit = None
    compu_inverse_value: Union[float, str] = None
    compu_const: Union[float, str] = None
    compu_rational_coeffs: CompuRationalCoeffs = None


class TexttableCompuMethod(CompuMethod):
    def __init__(self, internal_to_phys: List[CompuScale], internal_type):
        super().__init__(internal_type, DataType.A_UNICODE2STRING)
        self.internal_to_phys = internal_to_phys

        assert all(scale.lower_limit is not None or scale.upper_limit is not None
                   for scale in self.internal_to_phys), "Text table compu method doesn't have expected format!"

    @property
    def category(self):
        return "TEXTTABLE"

    def convert_physical_to_internal(self, physical_value):
        scale = next(filter(
            lambda scale: scale.compu_const == physical_value, self.internal_to_phys), None)
        if scale is not None:
            res = scale.compu_inverse_value if scale.compu_inverse_value is not None else scale.lower_limit.value
            assert isinstance(res, int)
            return res

    def __is_internal_in_scale(self, internal_value, scale: CompuScale):
        if scale.lower_limit.value is None:
            return internal_value == scale.lower_limit.value
        else:
            return scale.lower_limit.value <= internal_value and internal_value <= scale.lower_limit.value

    def convert_internal_to_physical(self, internal_value):
        try:
            scale = next(filter(lambda scale: self.__is_internal_in_scale(internal_value, scale),
                                self.internal_to_phys))
        except StopIteration:
            raise DecodeError(
                f"Texttable compu method could not decode {internal_value} to string.")
        return scale.compu_const

    def is_valid_physical_value(self, physical_value):
        return physical_value in map(lambda x: x.compu_const, self.internal_to_phys)

    def is_valid_internal_value(self, internal_value):
        return any(self.__is_internal_in_scale(internal_value, scale) for scale in self.internal_to_phys)

    def get_valid_physical_values(self):
        return list(map(lambda x: x.compu_const, self.internal_to_phys))


class LinearCompuMethod(CompuMethod):
    """Represents the decoding function d(y) = (offset + factor * y) / denominator
    where d(y) is the physical value and y is the internal value.

    Examples
    --------

    Define the decoding function `d(y) = 4+2*y` (or equivalent encoding `e(x) = floor((x-4)/2)`)
    on all integers `y` in the range -10..10 (and `x` in -16..25).

    ```python
    method = LinearCompuMethod(
        offset=4,
        factor=2,
        internal_type=DataType.A_INT32,
        physical_type=DataType.A_INT32,
        internal_lower_limit = Limit(-10, IntervalType.CLOSED),
        internal_upper_limit = Limit(11, IntervalType.OPEN)
    )
    ```

    Decode an internal value:

    ```python
    >>> method.convert_internal_to_physical(6)  # == 4+2*6
    16
    ```

    Encode a physical value:

    ```python
    >>> method.convert_physical_to_internal(6)  # == 6/2-2
    1
    ```

    Get physical limits:

    ```python
    >>> method.physical_lower_limit
    Limit(value=-16, interval_type=IntervalType.CLOSED)
    >>> method.physical_upper_limit
    Limit(value=26, interval_type=IntervalType.OPEN)
    ```

    (Note that there may be additional restrictions to valid physical values by the surrounding data object prop.
    For example, limits given by the bit length are not considered in the compu method.)
    """

    def __init__(self,
                 offset,
                 factor,
                 internal_type: Union[DataType, str],
                 physical_type: Union[DataType, str],
                 denominator=1,
                 internal_lower_limit: Optional[Limit] = None,
                 internal_upper_limit: Optional[Limit] = None):
        super().__init__(internal_type, physical_type)
        self.offset = offset
        self.factor = factor
        self.denominator = denominator

        self.internal_lower_limit = internal_lower_limit
        if internal_lower_limit is None or internal_lower_limit.interval_type == IntervalType.INFINITE:
            self.internal_lower_limit = Limit(float("-inf"),
                                              IntervalType.INFINITE)

        self.internal_upper_limit = internal_upper_limit
        if internal_upper_limit is None or internal_upper_limit.interval_type == IntervalType.INFINITE:
            self.internal_upper_limit = Limit(float("inf"),
                                              IntervalType.INFINITE)

        assert self.internal_lower_limit is not None and self.internal_upper_limit is not None
        assert denominator > 0 and type(denominator) == int

        self.__compute_physical_limits()

    @property
    def category(self):
        return "LINEAR"

    @property
    def physical_lower_limit(self):
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self):
        return self._physical_upper_limit

    def __compute_physical_limits(self):
        """Computes the physical limits and stores them in the properties
        self._physical_lower_limit and self._physical_upper_limit.
        This method is only called during the initialization of a LinearCompuMethod.
        """
        def convert_to_limit_to_physical(limit: Limit, is_upper_limit: bool):
            if limit.interval_type == IntervalType.INFINITE:
                return limit
            elif limit.interval_type == limit.interval_type.OPEN and self.internal_type.as_python_type() == int:
                closed_limit = limit.value - 1 if is_upper_limit else limit.value + 1
                return Limit(
                    value=self._convert_internal_to_physical(closed_limit),
                    interval_type=IntervalType.CLOSED
                )
            else:
                return Limit(
                    value=self._convert_internal_to_physical(limit.value),
                    interval_type=limit.interval_type
                )

        if self.factor >= 0:
            self._physical_lower_limit = convert_to_limit_to_physical(
                self.internal_lower_limit, False)
            self._physical_upper_limit = convert_to_limit_to_physical(
                self.internal_upper_limit, True)
        else:
            # If the factor is negative, the lower and upper limit are swapped
            self._physical_lower_limit = convert_to_limit_to_physical(
                self.internal_upper_limit, True)
            self._physical_upper_limit = convert_to_limit_to_physical(
                self.internal_lower_limit, False)

    def _convert_internal_to_physical(self, internal_value):
        if self.denominator is None:
            result = self.offset + self.factor * internal_value
        else:
            result = (self.offset + self.factor *
                      internal_value) / self.denominator

        if self.internal_type == DataType.A_FLOAT64 and self.physical_type in [DataType.A_INT32, DataType.A_UINT32]:
            result = round(result)
        return self.physical_type.cast(result)

    def convert_internal_to_physical(self, internal_value) -> Union[int, float]:
        assert self.is_valid_internal_value(internal_value) or internal_value in [
            self.internal_lower_limit.value, self.internal_upper_limit.value]
        return self._convert_internal_to_physical(internal_value)

    def convert_physical_to_internal(self, physical_value):
        assert self.is_valid_physical_value(
            physical_value), f"physical value {physical_value} of type {type(physical_value)} is not valid. Expected type {self.physical_type} with internal range {self.internal_lower_limit} to {self.internal_upper_limit}"
        if self.denominator is None:
            result = (physical_value - self.offset) / self.factor
        else:
            result = ((physical_value * self.denominator) -
                      self.offset) / self.factor

        if self.physical_type == DataType.A_FLOAT64 and self.internal_type in [DataType.A_INT32, DataType.A_UINT32]:
            result = round(result)
        return self.internal_type.cast(result)

    def is_valid_physical_value(self, physical_value):
        # Do type checks
        expected_type = self.physical_type.as_python_type()
        if expected_type == float and type(physical_value) not in [int, float]:
            return False
        elif expected_type != float and type(physical_value) != expected_type:
            return False

        # Compare to the limits
        if not self.physical_lower_limit.complies_to_lower(physical_value):
            return False
        if not self.physical_upper_limit.complies_to_upper(physical_value):
            return False
        return True

    def is_valid_internal_value(self, internal_value):
        expected_type = self.internal_type.as_python_type()
        if expected_type == float and type(internal_value) not in [int, float]:
            return False
        elif expected_type != float and type(internal_value) != expected_type:
            return False

        if not self.internal_lower_limit.complies_to_lower(internal_value):
            return False
        if not self.internal_upper_limit.complies_to_upper(internal_value):
            return False

        return True


class ScaleLinearCompuMethod(CompuMethod):
    def __init__(self, linear_methods: Iterable[LinearCompuMethod]):
        super().__init__(list(linear_methods)[0].internal_type,
                         list(linear_methods)[0].physical_type)
        self.linear_methods = list(linear_methods)
        logger.debug("Created scale linear compu method!")

    @property
    def category(self):
        return "SCALE-LINEAR"

    def convert_physical_to_internal(self, physical_value):
        assert self.is_valid_physical_value(physical_value), \
            f"cannot convert the invalid physical value {physical_value} of type {type(physical_value)}"
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

    if internal_type.as_python_type() == float or physical_type.as_python_type() == float:
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

# TODO: implement this properly!
class TabIntpCompuMethod(CompuMethod):
    def __init__(self,
                 internal_type,
                 physical_type):
        super().__init__(internal_type, physical_type)
        logger.debug("Created table interpolation compu method!")
        logger.warning(
            "TODO: Implement table interpolation compu method properly!")

    @property
    def category(self):
        return "TAB-INTP"

    def convert_physical_to_internal(self, physical_value):
        return self.internal_type.cast(physical_value)

    def convert_internal_to_physical(self, internal_value):
        return self.physical_type.cast(internal_value)

    def is_valid_physical_value(self, physical_value):
        return True

    def is_valid_internal_value(self, internal_value):
        return True


def read_limit_from_odx(et_element, internal_type: DataType):
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
                limit = Limit(int("0x" + et_element.text, 16), interval_type)
            elif internal_type.as_python_type() == float:
                limit = Limit(float(et_element.text), interval_type)
            else:
                limit = Limit(int(et_element.text, 10), interval_type)

    else:
        limit = None
    return limit


def read_compu_method_from_odx(et_element, internal_type: DataType, physical_type: DataType) -> CompuMethod:
    compu_category = et_element.find("CATEGORY").text
    assert compu_category in ["IDENTICAL", "LINEAR", "SCALE-LINEAR",
                              "TEXTTABLE", "COMPUCODE", "TAB-INTP",
                              "RAT-FUNC", "SCALE-RAT-FUNC"]

    if et_element.find("COMPU-PHYS-TO-INTERNAL") is not None:  # TODO: Is this never used?
        raise NotImplementedError(
            f"Found COMPU-PHYS-TO-INTERNAL for category {compu_category}")

    kwargs = {"internal_type": internal_type}

    if compu_category == "IDENTICAL":
        assert (internal_type == physical_type or (
            internal_type in [DataType.A_ASCIISTRING,  DataType.A_UTF8STRING] and physical_type == DataType.A_UNICODE2STRING)
        ), (f"Internal type '{internal_type}' and physical type '{physical_type}'"
            f" must be the same for compu methods of category '{compu_category}'")
        return IdenticalCompuMethod(internal_type=internal_type, physical_type=physical_type)

    if compu_category == "TEXTTABLE":
        assert physical_type == DataType.A_UNICODE2STRING
        compu_internal_to_phys = et_element.find("COMPU-INTERNAL-TO-PHYS")

        internal_to_phys = []
        for scale in compu_internal_to_phys.iterfind("COMPU-SCALES/COMPU-SCALE"):
            lower_limit = read_limit_from_odx(scale.find("LOWER-LIMIT"),
                                              internal_type=internal_type)
            upper_limit = read_limit_from_odx(scale.find("UPPER-LIMIT"),
                                              internal_type=internal_type)

            if scale.find("COMPU-INVERSE-VALUE/VT") is not None:
                compu_inverse_value = scale.find(
                    "COMPU-INVERSE-VALUE/VT"
                ).text
            elif scale.find("COMPU-INVERSE-VALUE/V") is not None:
                compu_inverse_value = float(
                    scale.find("COMPU-INVERSE-VALUE/V").text
                )
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
        assert all(isinstance(scale.lower_limit.value, int) or isinstance(scale.upper_limit.value, int)
                   for scale in internal_to_phys), "Text table compu method doesn't have expected format!"
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
        return TabIntpCompuMethod(internal_type=internal_type, physical_type=physical_type)

    # TODO: Implement other categories (never instantiate CompuMethod)
    logger.warning(
        f"Warning: Computation category {compu_category} is not implemented!")
    return CompuMethod()
