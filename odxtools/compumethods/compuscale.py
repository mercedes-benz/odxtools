# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import create_description_from_et
from .compurationalcoeffs import CompuRationalCoeffs
from .limit import Limit


@dataclass
class CompuScale:
    """A COMPU-SCALE represents one value range of a COMPU-METHOD.

    Example:

    For a TEXTTABLE compu method a compu scale within COMPU-INTERNAL-TO-PHYS
    can be defined with
    ```
    scale = CompuScale(
        short_label="example_label", # optional: provide a label
        description="<p>fancy description</p>", # optional: provide a description
        lower_limit=Limit(0), # required: lower limit
        upper_limit=Limit(3), # required: upper limit
        compu_inverse_value=2, # required if lower_limit != upper_limit
        compu_const="true", # required: physical value to be shown to the user
    )
    ```

    Almost all attributes are optional but there are compu-method-specific restrictions.
    E.g., lower_limit must always be defined unless the COMPU-METHOD is of CATEGORY LINEAR or RAT-FUNC.
    Either `compu_const` or `compu_rational_coeffs` must be defined but never both.
    """

    short_label: Optional[str]
    description: Optional[str]
    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]
    compu_inverse_value: Optional[AtomicOdxType]
    compu_const: Optional[AtomicOdxType]
    compu_rational_coeffs: Optional[CompuRationalCoeffs]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                internal_type: DataType, physical_type: DataType) -> "CompuScale":
        short_label = et_element.findtext("SHORT-LABEL")
        description = create_description_from_et(et_element.find("DESC"))
        lower_limit = Limit.from_et(et_element.find("LOWER-LIMIT"), internal_type=internal_type)
        upper_limit = Limit.from_et(et_element.find("UPPER-LIMIT"), internal_type=internal_type)

        compu_inverse_value = internal_type.create_from_et(et_element.find("COMPU-INVERSE-VALUE"))
        compu_const = physical_type.create_from_et(et_element.find("COMPU-CONST"))

        compu_rational_coeffs: Optional[CompuRationalCoeffs] = None
        if (crc_elem := et_element.find("COMPU-RATIONAL-COEFFS")) is not None:
            compu_rational_coeffs = CompuRationalCoeffs.from_et(crc_elem, doc_frags)

        return CompuScale(
            short_label=short_label,
            description=description,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            compu_inverse_value=compu_inverse_value,
            compu_const=compu_const,
            compu_rational_coeffs=compu_rational_coeffs)
