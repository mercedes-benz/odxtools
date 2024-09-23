# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional, cast
from xml.etree import ElementTree

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import dataclass_fields_asdict
from .compumethod import CompuCategory, CompuMethod
from .ratfuncsegment import RatFuncSegment


@dataclass
class RatFuncCompuMethod(CompuMethod):
    """A compu method using a rational function

    i.e. internal values are converted to physical ones using the
    function `f(x) = (a0 + a1*x + a2*x^2 ...)/(b0 + b0*x^2 ...)` where `f(x)`
    is the physical value and `x` is the internal value. In contrast
    to `ScaleRatFuncCompuMethod`, this compu method only exhibits a
    single segment)

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.5.
    """

    @property
    def int_to_phys_segment(self) -> RatFuncSegment:
        return self._int_to_phys_segment

    @property
    def phys_to_int_segment(self) -> Optional[RatFuncSegment]:
        return self._phys_to_int_segment

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "RatFuncCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return RatFuncCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        odxassert(self.category == CompuCategory.RAT_FUNC,
                  "RatFuncCompuMethod must exhibit RAT-FUNC category")

        odxassert(self.physical_type in [
            DataType.A_FLOAT32,
            DataType.A_FLOAT64,
            DataType.A_INT32,
            DataType.A_UINT32,
        ])
        odxassert(self.internal_type in [
            DataType.A_FLOAT32,
            DataType.A_FLOAT64,
            DataType.A_INT32,
            DataType.A_UINT32,
        ])

        if self.compu_internal_to_phys is None:
            odxraise("RAT-FUNC compu methods require COMPU-INTERNAL-TO-PHYS")
            return

        int_to_phys_scales = self.compu_internal_to_phys.compu_scales
        if len(int_to_phys_scales) != 1:
            odxraise("RAT-FUNC compu methods expect exactly one compu scale within "
                     "COMPU-INTERNAL-TO-PHYS")
            return cast(None, RatFuncCompuMethod)

        self._int_to_phys_segment = RatFuncSegment.from_compu_scale(
            int_to_phys_scales[0], value_type=self.physical_type)

        self._phys_to_int_segment = None
        if self.compu_phys_to_internal is not None:
            phys_to_int_scales = self.compu_phys_to_internal.compu_scales
            if len(phys_to_int_scales) != 1:
                odxraise("RAT-FUNC compu methods expect exactly one compu scale within "
                         "COMPU-PHYS-TO-INTERNAL")
                return cast(None, RatFuncCompuMethod)

            self._phys_to_int_segment = RatFuncSegment.from_compu_scale(
                phys_to_int_scales[0], value_type=self.internal_type)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if not self._int_to_phys_segment.applies(internal_value):
            odxraise(f"Cannot decode internal value {internal_value!r}", DecodeError)
            return cast(AtomicOdxType, None)

        return self._int_to_phys_segment.convert(internal_value)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        if self._phys_to_int_segment is None or not self._phys_to_int_segment.applies(
                physical_value):
            odxraise(f"Cannot encode physical value {physical_value!r}", EncodeError)
            return cast(AtomicOdxType, None)

        return self._phys_to_int_segment.convert(physical_value)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return self._phys_to_int_segment is not None and self._phys_to_int_segment.applies(
            physical_value)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return self._int_to_phys_segment.applies(internal_value)
