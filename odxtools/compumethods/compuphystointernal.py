# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..odxtypes import DataType
from ..progcode import ProgCode
from ..snrefcontext import SnRefContext
from .compudefaultvalue import CompuDefaultValue
from .compuscale import CompuScale


@dataclass
class CompuPhysToInternal:
    compu_scales: List[CompuScale]
    prog_code: Optional[ProgCode]
    compu_default_value: Optional[CompuDefaultValue]

    @staticmethod
    def compu_phys_to_internal_from_et(et_element: ElementTree.Element,
                                       doc_frags: List[OdxDocFragment], *, internal_type: DataType,
                                       physical_type: DataType) -> "CompuPhysToInternal":
        compu_scales = [
            CompuScale.compuscale_from_et(
                cse, doc_frags, domain_type=physical_type, range_type=internal_type)
            for cse in et_element.iterfind("COMPU-SCALES/COMPU-SCALE")
        ]

        prog_code = None
        if (pce := et_element.find("PROG-CODE")) is not None:
            prog_code = ProgCode.from_et(pce, doc_frags)

        compu_default_value = None
        if (cdve := et_element.find("COMPU-DEFAULT-VALUE")) is not None:
            compu_default_value = CompuDefaultValue.compuvalue_from_et(
                cdve, data_type=internal_type)

        return CompuPhysToInternal(
            compu_scales=compu_scales, prog_code=prog_code, compu_default_value=compu_default_value)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {}

        if self.prog_code is not None:
            result.update(self.prog_code._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.prog_code is not None:
            self.prog_code._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.prog_code is not None:
            self.prog_code._resolve_snrefs(context)
