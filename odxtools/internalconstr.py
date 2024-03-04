# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .compumethods.limit import Limit
from .odxlink import OdxDocFragment
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

    value_type: DataType

    @staticmethod
    def constr_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                       value_type: DataType) -> "InternalConstr":

        lower_limit = Limit.limit_from_et(
            et_element.find("LOWER-LIMIT"), doc_frags, value_type=value_type)
        upper_limit = Limit.limit_from_et(
            et_element.find("UPPER-LIMIT"), doc_frags, value_type=value_type)

        scale_constrs = [
            ScaleConstr.scale_constr_from_et(sc_el, doc_frags, value_type=value_type)
            for sc_el in et_element.iterfind("SCALE-CONSTRS/SCALE-CONSTR")
        ]

        return InternalConstr(
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            scale_constrs=scale_constrs,
            value_type=value_type)
