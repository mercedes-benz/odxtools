# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional, cast
from xml.etree import ElementTree

from ..exceptions import DecodeError, EncodeError, odxassert, odxraise
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..progcode import ProgCode
from ..utils import dataclass_fields_asdict
from .compumethod import CompuCategory, CompuMethod


@dataclass
class CompuCodeCompuMethod(CompuMethod):
    """A compu method specifies the tranfer functions using Java bytecode

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.9.
    """

    @property
    def internal_to_phys_code(self) -> Optional[ProgCode]:
        if self.compu_internal_to_phys is None:
            return None

        return self.compu_internal_to_phys.prog_code

    @property
    def phys_to_internal_code(self) -> Optional[ProgCode]:
        if self.compu_phys_to_internal is None:
            return None

        return self.compu_phys_to_internal.prog_code

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "CompuCodeCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        return CompuCodeCompuMethod(**kwargs)

    def __post_init__(self) -> None:
        odxassert(self.category == CompuCategory.COMPUCODE,
                  "CompuCodeCompuMethod must exhibit COMPUCODE category")

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        odxraise(r"CompuCodeCompuMethod cannot be executed by odxtools", DecodeError)
        return cast(AtomicOdxType, None)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        odxraise(r"CompuCodeCompuMethod cannot be executed by odxtools", EncodeError)
        return cast(AtomicOdxType, None)

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        # CompuCodeCompuMethod cannot be executed by odxtools
        return False

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        # CompuCodeCompuMethod cannot be executed by odxtools
        return False
