# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Tuple, Union

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
from ..odxtypes import AtomicOdxType, DataType
from .compumethod import CompuMethod, CompuMethodCategory
from .limit import IntervalType, Limit


@dataclass
class TabIntpCompuMethod(CompuMethod):
    """
    A compu method of type Tab Interpolated is used for linear interpolation.

    A `TabIntpCompuMethod` is defined by a set of points. Each point is an (internal, physical) value pair.
    When converting from internal to physical or vice-versa, the result is linearly interpolated.

    The function defined by a `TabIntpCompuMethod` is similar to the one of a `ScaleLinearCompuMethod` with the following differences:

    * `TabIntpCompuMethod`s are always continuous whereas `ScaleLinearCompuMethod` might have jumps
    * `TabIntpCompuMethod`s are always invertible: Even if the linear interpolation is not monotonic, the first matching interval is taken.

    Refer to ASAM MCD-2 D (ODX) Specification, section 7.3.6.6.8 for details.

    Examples
    --------

    Create a TabIntpCompuMethod defined by the points (0, -1), (10, 1), (30, 2)::

        method = TabIntpCompuMethod(
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32,
            internal_points=[0, 10, 30],
            physical_points=[-1, 1, 2]
        )

    Note that the points are given as two lists. The equivalent odx definition is::

        <COMPU-METHOD>
            <CATEGORY>TAB-INTP</CATEGORY>
            <COMPU-INTERNAL-TO-PHYS>
                <COMPU-SCALES>
                    <COMPU-SCALE>
                        <LOWER-LIMIT INTERVAL-TYPE = "CLOSED">0</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>-1</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                    <COMPU-SCALE>
                        <LOWER-LIMIT INTERVAL-TYPE = "CLOSED">10</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>1</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                    <COMPU-SCALE>
                        <LOWER-LIMIT INTERVAL-TYPE = "CLOSED">30</LOWER-LIMIT>
                        <COMPU-CONST>
                            <V>2</V>
                        </COMPU-CONST>
                    </COMPU-SCALE>
                </COMPU-SCALES>
            </COMPU-INTERNAL-TO-PHYS>
        </COMPU-METHOD>

    """

    internal_points: List[Union[float, int]]
    physical_points: List[Union[float, int]]

    def __post_init__(self) -> None:
        self._physical_lower_limit = Limit(min(self.physical_points), IntervalType.CLOSED)
        self._physical_upper_limit = Limit(max(self.physical_points), IntervalType.CLOSED)

        self._assert_validity()

    @property
    def category(self) -> CompuMethodCategory:
        return "TAB-INTP"

    @property
    def physical_lower_limit(self) -> Limit:
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self) -> Limit:
        return self._physical_upper_limit

    def _assert_validity(self) -> None:
        odxassert(len(self.internal_points) == len(self.physical_points))

        odxassert(
            self.internal_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
                DataType.A_FLOAT32,
                DataType.A_FLOAT64,
            ], "Internal data type of tab-intp compumethod must be one of"
            " [A_INT32, A_UINT32, A_FLOAT32, A_FLOAT64]")
        odxassert(
            self.physical_type in [
                DataType.A_INT32,
                DataType.A_UINT32,
                DataType.A_FLOAT32,
                DataType.A_FLOAT64,
            ], "Physical data type of tab-intp compumethod must be one of"
            " [A_INT32, A_UINT32, A_FLOAT32, A_FLOAT64]")

    def _piecewise_linear_interpolate(self, x: Union[int, float],
                                      points: List[Tuple[Union[int, float],
                                                         Union[int, float]]]) -> Union[float, None]:
        for ((x0, y0), (x1, y1)) in zip(points[:-1], points[1:]):
            if x0 <= x and x <= x1:
                return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

        return None

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        if not isinstance(physical_value, (int, float)):
            raise EncodeError("The type of values of tab-intp compumethods must "
                              "either int or float")

        reference_points = list(zip(self.physical_points, self.internal_points))
        odxassert(
            isinstance(physical_value, (int, float)),
            "Only integers and floats can be piecewise linearly interpolated")
        result = self._piecewise_linear_interpolate(
            physical_value,  # type: ignore[arg-type]
            reference_points)

        if result is None:
            raise EncodeError(f"Internal value {physical_value!r} must be inside the range"
                              f" [{min(self.physical_points)}, {max(self.physical_points)}]")
        res = self.internal_type.make_from(result)
        if not isinstance(res, (int, float)):
            odxraise()
        return res

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if not isinstance(internal_value, (int, float)):
            raise EncodeError("The internal type of values of tab-intp compumethods must "
                              "either int or float")

        reference_points = list(zip(self.internal_points, self.physical_points))
        result = self._piecewise_linear_interpolate(
            internal_value,  # type: ignore[arg-type]
            reference_points)

        if result is None:
            raise DecodeError(f"Internal value {internal_value!r} must be inside the range"
                              f" [{min(self.internal_points)}, {max(self.internal_points)}]")
        res = self.physical_type.make_from(result)
        if not isinstance(res, (int, float)):
            odxraise()
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
