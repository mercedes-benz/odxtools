# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, cast
from xml.etree import ElementTree

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import dataclass_fields_asdict
from .compumethod import CompuCategory, CompuMethod
from .compuscale import CompuScale


@dataclass
class TexttableCompuMethod(CompuMethod):
    """Text table compute methods translate numbers to human readable
    textual descriptions.

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.7.

    """

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "TexttableCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return TexttableCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        odxassert(self.category == CompuCategory.TEXTTABLE,
                  "TexttableCompuMethod must exhibit TEXTTABLE category")

        # the spec says that the physical data type shall be
        # A_UNICODE2STRING, but we are a bit more lenient and allow
        # any kind of string...
        odxassert(
            self.physical_type
            in [DataType.A_UNICODE2STRING, DataType.A_UTF8STRING, DataType.A_ASCIISTRING],
            "TEXTTABLE must have string type as its physical datatype.")

        if self.compu_internal_to_phys is None:
            odxraise("TEXTTABLE compu methods must exhibit a COMPU-INTERNAL-TO-PHYS subtag.")
            scales = []
        else:
            scales = self.compu_internal_to_phys.compu_scales

        odxassert(
            all(scale.lower_limit is not None or scale.upper_limit is not None for scale in scales),
            "All scales of TEXTTABLE compu methods must provide limits!")

        self._compu_physical_default_value = None
        citp = odxrequire(self.compu_internal_to_phys)
        if (cdv := citp.compu_default_value) is not None:
            self._compu_physical_default_value = self.physical_type.from_string(odxrequire(cdv.vt))

        self._compu_internal_default_value = None
        cpti = self.compu_phys_to_internal
        if cpti is not None and (cdv := cpti.compu_default_value) is not None:
            self._compu_internal_default_value = self.internal_type.from_string(odxrequire(cdv.v))

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        scales = []
        if (citp := self.compu_internal_to_phys) is not None:
            scales = citp.compu_scales
        matching_scales = [
            x for x in scales if x.compu_const is not None and x.compu_const.value == physical_value
        ]

        if len(matching_scales) == 0:
            if self._compu_internal_default_value is None:
                odxraise(f"Texttable could not encode {physical_value!r}.", EncodeError)
                return cast(None, AtomicOdxType)

            return self._compu_internal_default_value
        elif len(matching_scales) > 1:
            odxraise(f"Texttable could not uniquely encode {physical_value!r}.", EncodeError)

        scale = matching_scales[0]
        if scale.compu_inverse_value is not None and (civ :=
                                                      scale.compu_inverse_value.value) is not None:
            return civ
        elif scale.lower_limit is not None and scale.lower_limit._value is not None:
            return scale.lower_limit._value
        elif scale.upper_limit is not None and scale.upper_limit._value is not None:
            return scale.upper_limit._value

        odxraise(f"Texttable compu method could not encode '{physical_value!r}'.", EncodeError)

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        scales = []
        if (citp := self.compu_internal_to_phys) is not None:
            scales = citp.compu_scales
        matching_scales: List[CompuScale] = [x for x in scales if x.applies(internal_value)]

        if len(matching_scales) == 0:
            if self._compu_physical_default_value is None:
                odxraise(f"Texttable could not decode {internal_value!r}.", DecodeError)
                return cast(None, AtomicOdxType)

            return self._compu_physical_default_value

        if len(matching_scales) > 1:
            odxraise(f"Texttable could not uniquely decode {internal_value!r}.", DecodeError)

        scale = matching_scales[0]

        if scale.compu_const is None:
            odxraise(f"Encountered a COMPU-SCALE with no COMPU-CONST.")
            return cast(None, AtomicOdxType)

        if scale.compu_const.value is not None:
            return scale.compu_const.value

        odxraise(f"Texttable compu method could not decode '{internal_value!r}'.", EncodeError)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        if self._compu_physical_default_value is not None:
            return True

        scales = []
        if (cpti := self.compu_internal_to_phys) is not None:
            scales = cpti.compu_scales

        return any(scale.compu_const.value == physical_value
                   for scale in scales
                   if scale.compu_const is not None)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        if self._compu_internal_default_value is not None:
            return True

        scales = []
        if (citp := self.compu_internal_to_phys) is not None:
            scales = citp.compu_scales

        return any(scale.applies(internal_value) for scale in scales)
