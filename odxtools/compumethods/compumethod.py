# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from ..exceptions import odxraise
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType, DataType
from ..snrefcontext import SnRefContext
from .compuinternaltophys import CompuInternalToPhys
from .compuphystointernal import CompuPhysToInternal


class CompuCategory(Enum):
    IDENTICAL = "IDENTICAL"
    LINEAR = "LINEAR"
    SCALE_LINEAR = "SCALE-LINEAR"
    TEXTTABLE = "TEXTTABLE"
    COMPUCODE = "COMPUCODE"
    TAB_INTP = "TAB-INTP"
    RAT_FUNC = "RAT-FUNC"
    SCALE_RAT_FUNC = "SCALE-RAT-FUNC"


@dataclass
class CompuMethod:
    """A compu method translates between the internal representation
    of a value and their physical representation.

    There are many compu methods, but all of them are specified using
    the same mechanism: The conversion from internal to physical
    quantities is specified using the COMPU-INTERNAL-TO-PHYS subtag,
    and the inverse is covered by
    COMPU-PHYS-TO-INTERNAL. Alternatively to directly specifying the
    parameters needed for conversion, it is also possible to specify a
    Java program which does the conversion (doing this excludes using
    ODX in non-Java contexts, though).

    For details, refer to ASAM specification MCD-2 D (ODX), section 7.3.6.6.

    """

    category: CompuCategory
    compu_internal_to_phys: Optional[CompuInternalToPhys]
    compu_phys_to_internal: Optional[CompuPhysToInternal]

    physical_type: DataType
    internal_type: DataType

    @staticmethod
    def compu_method_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             internal_type: DataType, physical_type: DataType) -> "CompuMethod":
        cat_text = et_element.findtext("CATEGORY")
        if cat_text is None:
            odxraise("No category specified for compu method")
            cat_text = "IDENTICAL"

        try:
            category = CompuCategory(cat_text)
        except ValueError:
            odxraise(f"Encountered compu method of unknown category '{cat_text}'")
            category = CompuCategory.IDENTICAL

        compu_internal_to_phys = None
        if (citp_elem := et_element.find("COMPU-INTERNAL-TO-PHYS")) is not None:
            compu_internal_to_phys = CompuInternalToPhys.compu_internal_to_phys_from_et(
                citp_elem, doc_frags, internal_type=internal_type, physical_type=physical_type)
        compu_phys_to_internal = None
        if (cpti_elem := et_element.find("COMPU-PHYS-TO-INTERNAL")) is not None:
            compu_phys_to_internal = CompuPhysToInternal.compu_phys_to_internal_from_et(
                cpti_elem, doc_frags, internal_type=internal_type, physical_type=physical_type)

        return CompuMethod(
            category=category,
            compu_internal_to_phys=compu_internal_to_phys,
            compu_phys_to_internal=compu_phys_to_internal,
            physical_type=physical_type,
            internal_type=internal_type)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        if self.compu_internal_to_phys is not None:
            result.update(self.compu_internal_to_phys._build_odxlinks())

        if self.compu_phys_to_internal is not None:
            result.update(self.compu_phys_to_internal._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.compu_internal_to_phys is not None:
            self.compu_internal_to_phys._resolve_odxlinks(odxlinks)

        if self.compu_phys_to_internal is not None:
            self.compu_phys_to_internal._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.compu_internal_to_phys is not None:
            self.compu_internal_to_phys._resolve_snrefs(context)

        if self.compu_phys_to_internal is not None:
            self.compu_phys_to_internal._resolve_snrefs(context)

    def convert_physical_to_internal(self, physical_value: AtomicOdxType) -> AtomicOdxType:
        raise NotImplementedError()

    def convert_internal_to_physical(self, internal_value: AtomicOdxType) -> AtomicOdxType:
        raise NotImplementedError()

    def is_valid_physical_value(self, physical_value: AtomicOdxType) -> bool:
        raise NotImplementedError()

    def is_valid_internal_value(self, internal_value: AtomicOdxType) -> bool:
        raise NotImplementedError()
