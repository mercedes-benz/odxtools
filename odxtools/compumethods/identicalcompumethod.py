# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from ..exceptions import odxassert
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import dataclass_fields_asdict
from .compumethod import CompuMethod


@dataclass
class IdenticalCompuMethod(CompuMethod):
    """Identical compu methods just pass through the internal value.

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.2.
    """

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType,
                             physical_type: DataType) -> "IdenticalCompuMethod":
        cm = CompuMethod.compu_method_from_et(
            et_element, doc_frags, internal_type=internal_type, physical_type=physical_type)
        kwargs = dataclass_fields_asdict(cm)

        odxassert(
            internal_type == physical_type or
            (internal_type
             in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING, DataType.A_UNICODE2STRING] and
             physical_type
             in [DataType.A_ASCIISTRING, DataType.A_UTF8STRING, DataType.A_UNICODE2STRING]),
            f"Internal type and physical type must be the same for compu methods of category "
            f"'{cm.category}' (internal type: '{internal_type.value}', physical type: "
            f"'{physical_type.value}')")

        return IdenticalCompuMethod(**kwargs)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        return physical_value

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        return internal_value

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        return self.physical_type.isinstance(physical_value)

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        return self.internal_type.isinstance(internal_value)
