# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import List, Tuple, Union

from ..exceptions import EncodeError, DecodeError
from ..globals import logger
from ..odxtypes import DataType

from .compumethodbase import CompuMethod
from .limit import IntervalType, Limit


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

    def __init__(self,
                 internal_type: Union[DataType, str],
                 physical_type: Union[DataType, str],
                 internal_points: List[Union[float, int]],
                 physical_points: List[Union[float, int]]):
        super().__init__(internal_type, physical_type, "TAB-INTP")

        self.internal_points = internal_points
        self.physical_points = physical_points

        self._physical_lower_limit = Limit(
            min(physical_points), IntervalType.CLOSED)
        self._physical_upper_limit = Limit(
            max(physical_points), IntervalType.CLOSED)

        logger.debug("Created compu method of type tab interpolated !")
        self._assert_validity()

    @property
    def physical_lower_limit(self) -> Limit:
        return self._physical_lower_limit

    @property
    def physical_upper_limit(self) -> Limit:
        return self._physical_upper_limit

    def _assert_validity(self) -> None:
        assert len(self.internal_points) == len(self.physical_points)

        assert self.internal_type in [DataType.A_INT32, DataType.A_UINT32,
                                      DataType.A_FLOAT32, DataType.A_FLOAT64], \
            ("Internal data type of tab-intp compumethod must be one of"
             " [DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64]")
        assert self.physical_type in [DataType.A_INT32, DataType.A_UINT32,
                                      DataType.A_FLOAT32, DataType.A_FLOAT64], \
            ("Physical data type of tab-intp compumethod must be one of"
             " [DataType.A_INT32, DataType.A_UINT32, DataType.A_FLOAT32, DataType.A_FLOAT64]")

    def _piecewise_linear_interpolate(self,
                                      x: Union[int, float],
                                      points: List[Tuple[Union[int, float], Union[int, float]]]) \
            -> Union[float, None]:
        for ((x0, y0), (x1, y1)) in zip(points[:-1], points[1:]):
            if x0 <= x and x <= x1:
                return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

        return None

    def convert_physical_to_internal(self, physical_value: Union[int, float]) -> Union[int, float]:
        reference_points = list(zip(
            self.physical_points, self.internal_points))
        result = self._piecewise_linear_interpolate(
            physical_value, reference_points)

        if result is None:
            raise EncodeError(f"Internal value {physical_value} must be inside the range"
                              f" [{min(self.physical_points)}, {max(self.physical_points)}]")
        res = self.internal_type.make_from(result)
        assert isinstance(res, (int, float))
        return res

    def convert_internal_to_physical(self, internal_value: Union[int, float]) -> Union[int, float]:
        reference_points = list(zip(
            self.internal_points, self.physical_points))
        result = self._piecewise_linear_interpolate(
            internal_value, reference_points)

        if result is None:
            raise DecodeError(f"Internal value {internal_value} must be inside the range"
                              f" [{min(self.internal_points)}, {max(self.internal_points)}]")
        res = self.physical_type.make_from(result)
        assert isinstance(res, (int, float))
        return res

    def is_valid_physical_value(self, physical_value: Union[int, float]) -> bool:
        return min(self.physical_points) <= physical_value and physical_value <= max(self.physical_points)

    def is_valid_internal_value(self, internal_value: Union[int, float]) -> bool:
        return min(self.internal_points) <= internal_value and internal_value <= max(self.internal_points)
