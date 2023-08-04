# SPDX-License-Identifier: MIT
from typing import List, Optional
from xml.etree import ElementTree

from .odxlink import OdxDocFragment
from .specialdatagroup import SpecialDataGroup


def create_sdgs_from_et(et_element: Optional[ElementTree.Element],
                        doc_frags: List[OdxDocFragment]) -> List[SpecialDataGroup]:

    if not et_element:
        return []

    result = []
    for sdg_elem in et_element.iterfind("SDG"):
        result.append(SpecialDataGroup.from_et(sdg_elem, doc_frags))

    return result
