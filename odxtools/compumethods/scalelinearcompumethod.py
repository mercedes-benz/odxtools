# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Union, cast
from xml.etree import ElementTree

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import dataclass_fields_asdict
from .compumethod import CompuCategory, CompuMethod
from .linearsegment import LinearSegment


@dataclass
class ScaleLinearCompuMethod(CompuMethod):
    """A piecewise linear compu method which may feature discontinuities.

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.4.
    """

    @property
    def segments(self) -> List[LinearSegment]:
        return self._segments

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "ScaleLinearCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return ScaleLinearCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        self._segments: List[LinearSegment] = []

        odxassert(self.category == CompuCategory.SCALE_LINEAR,
                  "ScaleLinearCompuMethod must exibit SCALE-LINEAR category")

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
            odxraise("SCALE-LINEAR compu methods require COMPU-INTERNAL-TO-PHYS")
            return

        compu_scales = self.compu_internal_to_phys.compu_scales

        for scale in compu_scales:
            self._segments.append(
                LinearSegment.from_compu_scale(
                    scale, internal_type=self.internal_type, physical_type=self.physical_type))

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> Union[float, int]:
        applicable_segments = [
            seg for seg in self._segments if seg.physical_applies(physical_value)
        ]
        if not applicable_segments:
            odxraise(r"No applicable segment for value {physical_value} found", EncodeError)
            return cast(int, None)
        elif len(applicable_segments):
            odxraise(r"Multiple applicable segments for value {physical_value} found", EncodeError)

        seg = applicable_segments[0]
        return seg.convert_physical_to_internal(physical_value)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> Union[float, int]:
        applicable_segments = [
            seg for seg in self._segments if seg.internal_applies(internal_value)
        ]
        if not applicable_segments:
            odxraise(r"No applicable segment for value {internal_value} found", DecodeError)
            return cast(int, None)
        elif len(applicable_segments):
            odxraise(r"Multiple applicable segments for value {internal_value} found", DecodeError)

        seg = applicable_segments[0]
        return seg.convert_internal_to_physical(internal_value)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return any(True for seg in self._segments if seg.physical_applies(physical_value))

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return any(True for seg in self._segments if seg.internal_applies(internal_value))
