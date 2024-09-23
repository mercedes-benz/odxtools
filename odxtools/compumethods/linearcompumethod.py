# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, cast
from xml.etree import ElementTree

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import dataclass_fields_asdict
from .compumethod import CompuCategory, CompuMethod
from .linearsegment import LinearSegment


@dataclass
class LinearCompuMethod(CompuMethod):
    """A compu method which does linear interpoation

    i.e. internal values are converted to physical ones using the
    function `f(x) = (offset + factor * x)/denominator` where `f(x)`
    is the physical value and `x` is the internal value. In contrast
    to `ScaleLinearCompuMethod`, this compu method only exhibits a
    single segment)

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.3.
    """

    @property
    def segment(self) -> LinearSegment:
        return self._segment

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "LinearCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return LinearCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        odxassert(self.category == CompuCategory.LINEAR,
                  "LinearCompuMethod must exhibit LINEAR category")

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
            odxraise("LINEAR compu methods require COMPU-INTERNAL-TO-PHYS")
            return

        compu_scales = self.compu_internal_to_phys.compu_scales

        if len(compu_scales) == 0:
            odxraise("LINEAR compu methods expect at least one compu scale within "
                     "COMPU-INTERNAL-TO-PHYS")
            return cast(None, LinearCompuMethod)
        elif len(compu_scales) > 1:
            odxraise("LINEAR compu methods expect at most one compu scale within "
                     "COMPU-INTERNAL-TO-PHYS")

        scale = compu_scales[0]
        self._segment = LinearSegment.from_compu_scale(
            scale, internal_type=self.internal_type, physical_type=self.physical_type)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        if not self._segment.internal_applies(internal_value):
            odxraise(f"Cannot decode internal value {internal_value!r}", DecodeError)

        return self._segment.convert_internal_to_physical(internal_value)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        if not self._segment.physical_applies(physical_value):
            odxraise(f"Cannot decode physical value {physical_value!r}", EncodeError)

        return self._segment.convert_physical_to_internal(physical_value)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return self._segment.physical_applies(physical_value)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return self._segment.internal_applies(internal_value)
