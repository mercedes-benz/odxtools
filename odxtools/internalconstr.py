# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .compumethods.limit import Limit
from .odxtypes import DataType
from .scaleconstr import ScaleConstr


@dataclass
class InternalConstr:
    """This class represents INTERNAL-CONSTR objects.
    """

    # TODO: Enforce the internal and physical constraints.

    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]
    scale_constrs: List[ScaleConstr]

    @staticmethod
    def from_et(et_element: ElementTree.Element, internal_type: DataType) -> "InternalConstr":

        lower_limit = Limit.from_et(et_element.find("LOWER-LIMIT"), internal_type=internal_type)
        upper_limit = Limit.from_et(et_element.find("UPPER-LIMIT"), internal_type=internal_type)

        scale_constrs = [
            ScaleConstr.from_et(sc_el, internal_type)
            for sc_el in et_element.iterfind("SCALE-CONSTRS/SCALE-CONSTR")
        ]

        return InternalConstr(
            lower_limit=lower_limit, upper_limit=upper_limit, scale_constrs=scale_constrs)
