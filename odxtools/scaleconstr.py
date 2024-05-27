# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from xml.etree import ElementTree

from .compumethods.limit import Limit
from .description import Description
from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment
from .odxtypes import DataType


class ValidType(Enum):
    VALID = "VALID"
    NOT_VALID = "NOT-VALID"
    NOT_DEFINED = "NOT-DEFINED"
    NOT_AVAILABLE = "NOT-AVAILABLE"


@dataclass
class ScaleConstr:
    """This class represents a SCALE-CONSTR.
    """

    short_label: Optional[str]
    description: Optional[Description]
    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]
    validity: ValidType
    value_type: DataType

    @staticmethod
    def scale_constr_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                             value_type: DataType) -> "ScaleConstr":
        short_label = et_element.findtext("SHORT-LABEL")
        description = Description.from_et(et_element.find("DESC"), doc_frags)

        lower_limit = Limit.limit_from_et(
            et_element.find("LOWER-LIMIT"), doc_frags, value_type=value_type)
        upper_limit = Limit.limit_from_et(
            et_element.find("UPPER-LIMIT"), doc_frags, value_type=value_type)

        validity_str = odxrequire(et_element.get("VALIDITY"))
        try:
            validity = ValidType(validity_str)
        except ValueError:
            odxraise(f"Encountered unknown Validity '{validity_str}'")

        return ScaleConstr(
            short_label=short_label,
            description=description,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            validity=validity,
            value_type=value_type)
