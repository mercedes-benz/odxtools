# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from xml.etree import ElementTree

from .compumethods.limit import Limit
from .odxdoccontext import OdxDocContext
from .odxtypes import DataType
from .scaleconstr import ScaleConstr


@dataclass(kw_only=True)
class InternalConstr:
    """This class represents INTERNAL-CONSTR objects.
    """

    # TODO: Enforce the internal and physical constraints.

    lower_limit: Limit | None = None
    upper_limit: Limit | None = None
    scale_constrs: list[ScaleConstr] = field(default_factory=list)

    value_type: DataType

    @staticmethod
    def constr_from_et(et_element: ElementTree.Element, context: OdxDocContext, *,
                       value_type: DataType) -> "InternalConstr":

        lower_limit = Limit.limit_from_et(
            et_element.find("LOWER-LIMIT"), context, value_type=value_type)
        upper_limit = Limit.limit_from_et(
            et_element.find("UPPER-LIMIT"), context, value_type=value_type)

        scale_constrs = [
            ScaleConstr.scale_constr_from_et(sc_el, context, value_type=value_type)
            for sc_el in et_element.iterfind("SCALE-CONSTRS/SCALE-CONSTR")
        ]

        return InternalConstr(
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            scale_constrs=scale_constrs,
            value_type=value_type)
