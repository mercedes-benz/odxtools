# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from xml.etree import ElementTree

from .compumethods.limit import Limit
from .exceptions import odxraise, odxrequire
from .odxtypes import DataType
from .utils import create_description_from_et


class Validity(Enum):
    VALID = "VALID"
    NOT_VALID = "NOT-VALID"
    NOT_DEFINED = "NOT-DEFINED"
    NOT_AVAILABLE = "NOT-AVAILABLE"


@dataclass
class ScaleConstr:
    """This class represents a SCALE-CONSTR.
    """

    short_label: Optional[str]
    description: Optional[str]
    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]
    validity: Validity

    @staticmethod
    def from_et(et_element: ElementTree.Element, internal_type: DataType) -> "ScaleConstr":
        short_label = et_element.findtext("SHORT-LABEL")
        description = create_description_from_et(et_element.find("DESC"))

        lower_limit = Limit.from_et(et_element.find("LOWER-LIMIT"), internal_type=internal_type)
        upper_limit = Limit.from_et(et_element.find("UPPER-LIMIT"), internal_type=internal_type)

        validity_str = odxrequire(et_element.get("VALIDITY"))
        try:
            validity = Validity(validity_str)
        except ValueError:
            odxraise(f"Encountered unknown Validity '{validity_str}'")

        return ScaleConstr(
            short_label=short_label,
            description=description,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            validity=validity)


@dataclass
class InternalConstr:
    """This class represents a INTERNAL-CONSTR.
    """

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
