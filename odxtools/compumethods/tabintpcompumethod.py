# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Union
from xml.etree import ElementTree

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import dataclass_fields_asdict
from .compumethod import CompuCategory, CompuMethod
from .limit import IntervalType, Limit


@dataclass
class TabIntpCompuMethod(CompuMethod):
    """A table-based interpolated compu method provides a continuous
    transfer function based on piecewise linear interpolation.

    A `TabIntpCompuMethod` is defined by a set of points. Each point
    is an (internal, physical) value pair.  When converting from
    internal to physical or vice-versa, the result is linearly
    interpolated.

    The function defined by a `TabIntpCompuMethod` is similar to the
    one of a `ScaleLinearCompuMethod` with the following differences:

    * `TabIntpCompuMethod`s are always continuous whereas
      `ScaleLinearCompuMethod` might exhibit gaps
    * `TabIntpCompuMethod`s are always invertible: Even if the linear
      interpolation is not monotonic, the first matching interval is
      used.

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.8.

    """

    @property
    def internal_points(self) -> List[Union[float, int]]:
        return self._internal_points

    @property
    def physical_points(self) -> List[Union[float, int]]:
        return self._physical_points

    @property
    def internal_lower_limit(self) -> Limit:
        return self._internal_lower_limit

    @property
    def internal_upper_limit(self) -> Limit:
        return self._internal_upper_limit

    @property
    def physical_lower_limit(self) -> Limit:
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self) -> Limit:
        return self._physical_upper_limit

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "TabIntpCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return TabIntpCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        odxassert(self.category == CompuCategory.TAB_INTP,
                  "TabIntpCompuMethod must exibit TAB-INTP category")

        self._internal_points: List[Union[int, float]] = []
        self._physical_points: List[Union[int, float]] = []
        for scale in odxrequire(self.compu_internal_to_phys).compu_scales:
            internal_point = odxrequire(scale.lower_limit).value
            physical_point = odxrequire(scale.compu_const).value

            if not isinstance(internal_point, (float, int)):
                odxraise("The type of values of tab-intp compumethods must "
                         "either int or float")
            if not isinstance(physical_point, (float, int)):
                odxraise("The type of values of tab-intp compumethods must "
                         "either int or float")

            self._internal_points.append(internal_point)
            self._physical_points.append(physical_point)

        self._physical_lower_limit = Limit(
            value_raw=str(min(self._physical_points)),
            value_type=self.physical_type,
            interval_type=IntervalType.CLOSED)
        self._physical_upper_limit = Limit(
            value_raw=str(max(self._physical_points)),
            value_type=self.physical_type,
            interval_type=IntervalType.CLOSED)

        self._internal_lower_limit = Limit(
            value_raw=str(min(self._internal_points)),
            value_type=self.internal_type,
            interval_type=IntervalType.CLOSED)
        self._internal_upper_limit = Limit(
            value_raw=str(max(self._internal_points)),
            value_type=self.internal_type,
            interval_type=IntervalType.CLOSED)

        self.__assert_validity()

    def __assert_validity(self) -> None:
        odxassert(len(self.internal_points) == len(self.physical_points))

        odxassert(
            self.internal_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
                DataType.A_FLOAT32,
                DataType.A_FLOAT64,
            ], "Internal data type of TAB-INTP compumethod must be one of"
            " [A_INT32, A_UINT32, A_FLOAT32, A_FLOAT64]")
        odxassert(
            self.physical_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
                DataType.A_FLOAT32,
                DataType.A_FLOAT64,
            ], "Physical data type of TAB-INTP compumethod must be one of"
            " [A_INT32, A_UINT32, A_FLOAT32, A_FLOAT64]")

    def __piecewise_linear_interpolate(self, x: Union[int, float],
                                       range_samples: List[Union[int, float]],
                                       domain_samples: List[Union[int,
                                                                  float]]) -> Union[float, None]:
        for i in range(0, len(range_samples) - 1):
            if (x0 := range_samples[i]) <= x and x <= (x1 := range_samples[i + 1]):
                y0 = domain_samples[i]
                y1 = domain_samples[i + 1]
                return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

        return None

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        if not isinstance(physical_value, (int, float)):
            odxraise("The type of values of tab-intp compumethods must "
                     "either int or float", EncodeError)
            return None

        odxassert(
            isinstance(physical_value, (int, float)),
            "Only integers and floats can be piecewise linearly interpolated", EncodeError)
        result = self.__piecewise_linear_interpolate(physical_value, self._physical_points,
                                                     self._internal_points)

        if result is None:
            odxraise(
                f"Internal value {physical_value!r} must be inside the range"
                f" [{min(self.physical_points)}, {max(self.physical_points)}]", EncodeError)

        res = self.internal_type.make_from(result)

        return res

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if not isinstance(internal_value, (int, float)):
            odxraise(
                "The internal type of values of tab-intp compumethods must "
                "either int or float", EncodeError)
            return None

        odxassert(
            isinstance(internal_value, (int, float)),
            "Only integers and floats can be piecewise linearly interpolated", DecodeError)

        result = self.__piecewise_linear_interpolate(internal_value, self._internal_points,
                                                     self._physical_points)

        if result is None:
            odxraise(
                f"Internal value {internal_value!r} must be inside the range"
                f" [{min(self.internal_points)}, {max(self.internal_points)}]", DecodeError)
            return None

        res = self.physical_type.make_from(result)

        return res

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        if not isinstance(physical_value, (int, float)):
            return False

        return min(self.physical_points) <= physical_value and physical_value <= max(
            self.physical_points)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        if not isinstance(internal_value, (int, float)):
            return False

        return min(self.internal_points) <= internal_value and internal_value <= max(
            self.internal_points)
