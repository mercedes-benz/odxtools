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
class ScaleRatFuncCompuMethod(CompuMethod):
    """A compu method using a piecewise rational function

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.5.
    """

    @property
    def int_to_phys_segments(self) -> List[RatFuncSegment]:
        return self._int_to_phys_segments

    @property
    def phys_to_int_segments(self) -> Optional[List[RatFuncSegment]]:
        return self._phys_to_int_segments

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "ScaleRatFuncCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return ScaleRatFuncCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        odxassert(self.category == CompuCategory.SCALE_RAT_FUNC,
                  "ScaleRatFuncCompuMethod must exhibit SCALE-RAT-FUNC category")

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
        if len(int_to_phys_scales) < 1:
            odxraise("RAT-FUNC compu methods expect at least one compu scale within "
                     "COMPU-INTERNAL-TO-PHYS")
            return

        self._int_to_phys_segments = [
            RatFuncSegment.from_compu_scale(scale, value_type=self.physical_type)
            for scale in int_to_phys_scales
        ]

        self._phys_to_int_segments = None
        if self.compu_phys_to_internal is not None:
            phys_to_int_scales = self.compu_phys_to_internal.compu_scales
            if len(phys_to_int_scales) < 1:
                odxraise("SCALE-RAT-FUNC compu methods expect at least one compu scale within "
                         "COMPU-PHYS-TO-INTERNAL")
                return

            self._phys_to_int_segments = [
                RatFuncSegment.from_compu_scale(scale, value_type=self.internal_type)
                for scale in phys_to_int_scales
            ]

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        for seg in self._int_to_phys_segments:
            if seg.applies(internal_value):
                return seg.convert(internal_value)

        odxraise(f"Internal value {internal_value!r} be decoded using this compumethod",
                 DecodeError)
        return cast(AtomicOdxType, None)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        if self._phys_to_int_segments is None:
            odxraise(f"Physical values cannot be encoded using this compumethod", EncodeError)
            return cast(AtomicOdxType, None)

        for seg in self._phys_to_int_segments:
            if seg.applies(physical_value):
                return seg.convert(physical_value)

        odxraise(f"Physical values {physical_value!r} be decoded using this compumethod",
                 EncodeError)
        return cast(AtomicOdxType, None)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return any(seg.applies(internal_value) for seg in self._int_to_phys_segments)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        if self._phys_to_int_segments is None:
            return False

        return any(seg.applies(physical_value) for seg in self._phys_to_int_segments)
